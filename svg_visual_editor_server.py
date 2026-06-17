#!/usr/bin/env python3
"""SVG 可视化编辑器 —— 本地后端服务。

仓库根目录的 ``SVG可视化编辑器.html`` 是一个纯前端页面,但它在设计上依赖一个
本地后端(基址 ``/api/projects``)来完成三类工作:列出/读写 projects 下的 SVG、
把 SVG 里以 ``../images/xxx.png`` 形式引用的本地素材通过 HTTP 提供出去、以及调用
``svg_to_pptx.py`` 导出 PPTX。此前该后端在仓库中缺失,直接导致两个现象:

1. 内嵌 ``data:`` base64 图能显示,但以相对路径引用的本地素材全部 404 —— 表现为
   “有些本地素材显示不出来”。
2. 导出按钮 POST ``/api/projects/export-pptx`` 因无后端而必然失败。

本服务补齐这套接口,与前端契约严格对齐:

    GET  /                          返回编辑器页面(SVG可视化编辑器.html)
    GET  /api/projects/meta         返回项目根标识 {project_root}
    GET  /api/projects/files        列出 projects 下所有可编辑 SVG
    GET  /api/projects/file?path=   读取单个 SVG 文本 {content}
    POST /api/projects/file         写回单个 SVG {path, content}
    GET  /api/projects/raw/<path>   提供本地素材(图片等)原始字节
    POST /api/projects/export-pptx  调用 svg_to_pptx.py 导出并回传 .pptx
    POST /api/projects/ai-edit      二次 AI 编辑:把当前 SVG + 自然语言指令交给大模型,
                                    以 SSE 流式回传改后的整页 SVG

用法:
    python3 svg_visual_editor_server.py
    python3 svg_visual_editor_server.py --projects-root projects --port 5060
    python3 svg_visual_editor_server.py --no-browser

依赖:
    flask>=3.0.0(仓库内 svg_editor/server.py 已使用,无需额外安装)
    anthropic(可选,仅启用右侧「AI 二次编辑」面板时需要;惰性导入,缺失不影响其余接口)

环境变量(AI 面板相关,均可选):
    ANTHROPIC_API_KEY   Claude API 凭证(启用 AI 面板必需)
    ANTHROPIC_BASE_URL  自定义 API 基址(走内网代理时设置)
    SVG_AI_MODEL        覆盖默认模型,默认 claude-opus-4-8
"""

import argparse
import json
import os
import subprocess
import sys
import threading
import time
import webbrowser
from pathlib import Path
from urllib.parse import quote

from flask import (
    Flask,
    Response,
    jsonify,
    request,
    send_file,
    send_from_directory,
    stream_with_context,
)

# 仓库根目录:本脚本所在目录即为根。编辑器页面与 svg_to_pptx.py 均据此定位。
_REPO_ROOT = Path(__file__).resolve().parent
_EDITOR_HTML = _REPO_ROOT / 'SVG可视化编辑器.html'
_SVG_TO_PPTX = _REPO_ROOT / 'skills' / 'ppt-master' / 'scripts' / 'svg_to_pptx.py'

# 列出 SVG 时仅纳入这些源目录下的文件。
_SOURCE_DIR_NAMES = ('svg_output', 'svg_final')
# 这些目录段一旦出现即整条排除:backup 快照内的 SVG 其 ../images/ 指向备份内不存在
# 的素材(会误报 404),exports 是产物目录,均非可编辑源。
_EXCLUDED_DIR_NAMES = ('backup', 'exports')
# 导出时用于反推“项目根目录”的源目录名(SVG 的上一级)。
_EXPORT_SOURCE_DIRS = ('svg_output', 'svg_final')
# 导出超时上限(秒),避免后台进程卡死请求线程。
_EXPORT_TIMEOUT = 600

# AI 二次编辑默认模型;可被环境变量 SVG_AI_MODEL 覆盖。仓库面向 Claude 生态,默认用最新
# Opus。凭证(ANTHROPIC_API_KEY)与可选代理基址(ANTHROPIC_BASE_URL)由 anthropic SDK
# 自动从环境读取,本服务不持久化任何密钥。
_DEFAULT_AI_MODEL = 'claude-opus-4-8'
# AI 生成上限。整页 SVG 可能较长,给足空间;流式输出规避 HTTP 超时。
_AI_MAX_TOKENS = 64000
# system 提示:稳定文本,作为前缀缓存(prompt caching),只描述任务约束,不含易变内容。
_AI_SYSTEM_PROMPT = (
    "You are an expert SVG editor for presentation slides. You receive one complete "
    "SVG document and one natural-language edit instruction. Return ONLY the complete, "
    "modified SVG document and nothing else: no markdown code fences, no explanation, "
    "no commentary before or after. The output MUST start with '<svg' (or an XML "
    "declaration followed by '<svg') and end with '</svg>'.\n\n"
    "Hard constraints:\n"
    "- Preserve the root viewBox, width and height unless the instruction explicitly "
    "asks to change the canvas size.\n"
    "- Preserve existing element structure, ids, fonts, gradients/defs and all "
    "'../images/...' asset references, unless the instruction requires changing them.\n"
    "- Make the smallest change that satisfies the instruction; do not restyle or "
    "re-layout unrelated elements.\n"
    "- Keep the result valid, self-contained SVG that renders the same way except for "
    "the requested change."
)


def _safe_join(root: Path, relative: str) -> Path | None:
    """把相对路径安全地拼接到 root 下,越权(路径穿越)时返回 None。

    ``resolve()`` 后用 ``relative_to`` 校验是权威的防穿越手段:任何 ``..`` 逃逸到
    root 之外都会触发 ``ValueError``。空路径或绝对路径一律拒绝。
    """
    if not relative:
        return None
    candidate = (root / relative).resolve()
    try:
        candidate.relative_to(root.resolve())
    except ValueError:
        return None
    return candidate


def _list_project_svgs(projects_root: Path) -> list[dict]:
    """收集 projects 下所有位于 svg_output/ 或 svg_final/ 内的 SVG。

    返回的 ``relative_path`` 相对 projects_root,使用 POSIX 斜杠,直接对应前端
    ``relativePath``;``file_name`` 为文件名。结果按路径排序,保证列表稳定。
    """
    if not projects_root.exists():
        return []
    files: list[dict] = []
    for svg_path in projects_root.rglob('*.svg'):
        if not svg_path.is_file():
            continue
        parts = svg_path.relative_to(projects_root).parts
        # 排除 backup/ 快照与 exports/ 产物目录。
        if any(name in parts for name in _EXCLUDED_DIR_NAMES):
            continue
        # 必须落在某个已知源目录内。
        if not any(name in parts for name in _SOURCE_DIR_NAMES):
            continue
        relative = svg_path.relative_to(projects_root).as_posix()
        files.append({'file_name': svg_path.name, 'relative_path': relative})
    files.sort(key=lambda item: item['relative_path'])
    return files


def _infer_project_dir(projects_root: Path, relative_path: str) -> Path | None:
    """从 SVG 的相对路径反推所属项目目录。

    约定布局为 ``<project>/(svg_output|svg_final)/<page>.svg``,因此项目目录即源
    目录的上一级。找不到源目录段时,退化为“去掉文件名与其父目录”的保守推断。
    """
    safe = _safe_join(projects_root, relative_path)
    if safe is None:
        return None
    parts = safe.relative_to(projects_root.resolve()).parts
    for source_name in _EXPORT_SOURCE_DIRS:
        if source_name in parts:
            index = parts.index(source_name)
            if index >= 1:
                return projects_root.resolve().joinpath(*parts[:index])
    # 退化路径:至少需要 <project>/<dir>/<file> 三段。
    if len(parts) >= 3:
        return projects_root.resolve().joinpath(*parts[:-2])
    return None


def _infer_source_dir(relative_path: str) -> str:
    """从 SVG 相对路径判断它属于哪个源目录,返回 'final' / 'output' / ''。

    用于导出 source=auto:让 svg_to_pptx 读取用户实际编辑的那个目录(``svg_final``
    或 ``svg_output``),而不是脚本的固定默认值,从而保证保存的修改进入导出结果。
    """
    parts = Path(relative_path).parts
    if 'svg_final' in parts:
        return 'final'
    if 'svg_output' in parts:
        return 'output'
    return ''


def create_app(projects_root: Path) -> Flask:
    """创建并配置 Flask 应用。``projects_root`` 为 projects 目录绝对路径。"""
    projects_root = projects_root.resolve()
    app = Flask(__name__)

    @app.route('/')
    def index():
        # 编辑器页面文件名含中文,用绝对路径直接回传,避免静态目录的编码问题。
        if not _EDITOR_HTML.exists():
            return jsonify({'error': f'编辑器页面缺失: {_EDITOR_HTML.name}'}), 404
        return send_file(str(_EDITOR_HTML))

    @app.route('/api/projects/meta')
    def project_meta():
        return jsonify({'project_root': projects_root.name or 'projects'})

    @app.route('/api/projects/files')
    def project_files():
        return jsonify({'files': _list_project_svgs(projects_root)})

    @app.route('/api/projects/file', methods=['GET', 'POST'])
    def project_file():
        if request.method == 'GET':
            relative = request.args.get('path', '')
            target = _safe_join(projects_root, relative)
            if target is None or not target.is_file():
                return jsonify({'error': '文件不存在或路径非法'}), 404
            try:
                content = target.read_text(encoding='utf-8')
            except OSError as exc:
                return jsonify({'error': f'读取失败: {exc}'}), 500
            return jsonify({'content': content})

        # POST:写回 SVG。仅允许覆盖已存在的 .svg,杜绝越权创建任意文件。
        data = request.get_json(silent=True) or {}
        relative = data.get('path', '')
        content = data.get('content')
        if not isinstance(content, str):
            return jsonify({'error': 'content 必须为字符串'}), 400
        target = _safe_join(projects_root, relative)
        if target is None or target.suffix.lower() != '.svg':
            return jsonify({'error': '路径非法或非 .svg 文件'}), 400
        if not target.exists():
            return jsonify({'error': '目标文件不存在,拒绝创建'}), 404
        try:
            target.write_text(content, encoding='utf-8')
        except OSError as exc:
            return jsonify({'error': f'写入失败: {exc}'}), 500
        return jsonify({'status': 'ok'})

    @app.route('/api/projects/raw/<path:subpath>')
    def project_raw(subpath: str):
        """提供 projects 下任意素材的原始字节(图片、字体等)。

        前端把 SVG 内 ``../images/x.png`` 解析为 ``/api/projects/raw/<项目>/images/x.png``,
        因此这里按 projects_root 为根直接定位文件,并做防穿越校验。
        """
        target = _safe_join(projects_root, subpath)
        if target is None or not target.is_file():
            return jsonify({'error': '素材不存在'}), 404
        return send_from_directory(
            str(target.parent), target.name, max_age=0,
        )

    @app.route('/api/projects/export-pptx', methods=['POST'])
    def export_pptx():
        data = request.get_json(silent=True) or {}
        relative_path = data.get('relative_path', '')
        project_dir = _infer_project_dir(projects_root, relative_path)
        if project_dir is None or not project_dir.is_dir():
            return jsonify({'error': '无法定位项目目录,请从左侧项目列表打开 SVG'}), 400

        source = (data.get('source') or 'auto').strip().lower()
        # auto:按用户打开/编辑的文件所在目录选择源,避免“在 svg_final/ 改了却导出
        # svg_output/ 旧内容”的错配。svg_to_pptx 的 native 默认读 svg_output,而编辑器
        # 常打开 svg_final,二者不一致会让保存的修改丢失在导出之外。
        if source not in ('final', 'output'):
            source = _infer_source_dir(relative_path)
        no_notes = bool(data.get('no_notes'))
        quiet = bool(data.get('quiet'))
        transition = data.get('transition')
        transition_duration = data.get('transition_duration')

        # 组装 svg_to_pptx.py 命令行。仍无法判定来源时不传 -s,沿用脚本默认。
        cmd = [sys.executable, str(_SVG_TO_PPTX), str(project_dir)]
        if source in ('final', 'output'):
            cmd += ['-s', source]
        if no_notes:
            cmd += ['--no-notes']
        if quiet:
            cmd += ['-q']
        if transition and transition != 'none':
            cmd += ['-t', str(transition)]
        if transition_duration not in (None, ''):
            cmd += ['--transition-duration', str(transition_duration)]

        exports_dir = project_dir / 'exports'
        before = _snapshot_pptx(exports_dir)
        started = time.time()
        try:
            result = subprocess.run(
                cmd, cwd=str(_REPO_ROOT), capture_output=True,
                text=True, timeout=_EXPORT_TIMEOUT,
            )
        except subprocess.TimeoutExpired:
            return jsonify({'error': f'导出超时(>{_EXPORT_TIMEOUT}s)'}), 504
        if result.returncode != 0:
            detail = (result.stderr or result.stdout or '').strip()
            return jsonify({'error': f'svg_to_pptx 失败: {detail[-800:]}'}), 500

        produced = _newest_pptx(exports_dir, before, started)
        if produced is None:
            return jsonify({'error': '未找到导出的 PPTX 文件'}), 500

        # 下载名:优先用户指定 output_name(补全 .pptx),否则用脚本产物名。
        output_name = (data.get('output_name') or '').strip()
        download_name = output_name or produced.name
        if not download_name.lower().endswith('.pptx'):
            download_name += '.pptx'

        response = send_file(
            str(produced),
            mimetype='application/vnd.openxmlformats-officedocument.presentationml.presentation',
            as_attachment=True,
            download_name=download_name,
        )
        # 前端用正则解析 filename*=UTF-8''<...>,显式补一条以兼容中文文件名。
        response.headers['Content-Disposition'] = (
            f"attachment; filename*=UTF-8''{quote(download_name)}"
        )
        return response

    @app.route('/api/projects/ai-edit', methods=['POST'])
    def ai_edit():
        """二次 AI 编辑:把当前 SVG 与指令交给大模型,SSE 流式回传改后的整页 SVG。

        请求体 ``{instruction, svg, relative_path?}``:``svg`` 为前端 serializeCurrentSVG()
        的当前内容(含未保存改动)。响应为 ``text/event-stream``,事件类型:
            delta  增量文本(模型逐字输出),``{text}``
            done   生成完成,``{svg}`` 为抽取出的完整 SVG
            error  失败,``{message}`` 为中文提示

        密钥与代理基址由 anthropic SDK 自动从环境读取;本服务不接收也不持久化密钥。
        """
        data = request.get_json(silent=True) or {}
        instruction = (data.get('instruction') or '').strip()
        svg = data.get('svg')
        if not instruction:
            return jsonify({'error': '指令不能为空'}), 400
        if not isinstance(svg, str) or '<svg' not in svg:
            return jsonify({'error': '缺少有效的 SVG 内容'}), 400

        def stream():
            # 惰性导入:未装 anthropic 时仅 AI 面板不可用,其余接口与服务不受影响。
            try:
                import anthropic
            except ImportError:
                yield _sse_event('error', {
                    'message': '后端未安装 anthropic,请执行 pip install anthropic 后重试',
                })
                return
            if not (os.environ.get('ANTHROPIC_API_KEY')
                    or os.environ.get('ANTHROPIC_AUTH_TOKEN')):
                yield _sse_event('error', {
                    'message': '未配置 ANTHROPIC_API_KEY,无法调用模型',
                })
                return

            model = os.environ.get('SVG_AI_MODEL', _DEFAULT_AI_MODEL)
            user_content = f'编辑指令:{instruction}\n\n当前 SVG:\n{svg}'
            collected: list[str] = []
            try:
                client = anthropic.Anthropic()
                with client.messages.stream(
                    model=model,
                    max_tokens=_AI_MAX_TOKENS,
                    thinking={'type': 'adaptive'},
                    system=[{
                        'type': 'text',
                        'text': _AI_SYSTEM_PROMPT,
                        'cache_control': {'type': 'ephemeral'},
                    }],
                    messages=[{'role': 'user', 'content': user_content}],
                ) as model_stream:
                    for text in model_stream.text_stream:
                        if text:
                            collected.append(text)
                            yield _sse_event('delta', {'text': text})
            except anthropic.APIStatusError as exc:
                yield _sse_event('error', {
                    'message': f'模型调用失败(HTTP {exc.status_code}):{exc.message}',
                })
                return
            except anthropic.APIError as exc:
                yield _sse_event('error', {'message': f'模型调用出错:{exc}'})
                return
            except Exception as exc:  # noqa: BLE001 — 兜底,保证连接以 error 收尾
                yield _sse_event('error', {'message': f'生成异常:{exc}'})
                return

            final_svg = _extract_svg(''.join(collected))
            if final_svg is None:
                yield _sse_event('error', {
                    'message': '模型未返回有效的 SVG,请调整指令后重试',
                })
                return
            yield _sse_event('done', {'svg': final_svg})

        headers = {
            'Cache-Control': 'no-cache',
            'X-Accel-Buffering': 'no',  # 关闭反向代理缓冲,确保逐块到达
        }
        return Response(
            stream_with_context(stream()),
            mimetype='text/event-stream',
            headers=headers,
        )

    return app


def _sse_event(event: str, payload: dict) -> str:
    """把一个事件编码为 SSE 帧。前端按 event 名分流,data 为单行 JSON。"""
    return f'event: {event}\ndata: {json.dumps(payload, ensure_ascii=False)}\n\n'


def _extract_svg(text: str) -> str | None:
    """从模型输出中抽取完整 SVG:剥掉 markdown 围栏,截取首个 <svg 到最后 </svg>。

    模型偶尔会包裹 ```svg 围栏或夹带零星说明,这里只信任 <svg>...</svg> 区间,
    取不到则返回 None,由调用方以 error 收尾。
    """
    if not text:
        return None
    cleaned = text.strip()
    start = cleaned.find('<svg')
    end = cleaned.rfind('</svg>')
    if start == -1 or end == -1 or end <= start:
        return None
    tail = end + len('</svg>')
    # 若 <svg 前存在 XML 声明,一并保留,便于下游解析。
    decl_start = cleaned.rfind('<?xml', 0, start)
    if decl_start != -1:
        return cleaned[decl_start:tail]
    return cleaned[start:tail]


def _snapshot_pptx(exports_dir: Path) -> set[str]:
    """记录导出前 exports/ 已有的 .pptx,用于事后甄别本次新产物。"""
    if not exports_dir.exists():
        return set()
    return {p.name for p in exports_dir.glob('*.pptx')}


def _newest_pptx(exports_dir: Path, before: set[str], started: float) -> Path | None:
    """挑选本次导出新生成(或刚被覆盖)的 PPTX。

    优先取“导出前不存在”的新文件;若用户用了固定输出名导致同名覆盖,则回退到
    “修改时间晚于本次启动”的最新文件,确保仍能返回正确产物。
    """
    if not exports_dir.exists():
        return None
    candidates = list(exports_dir.glob('*.pptx'))
    if not candidates:
        return None
    fresh = [p for p in candidates if p.name not in before]
    if not fresh:
        fresh = [p for p in candidates if p.stat().st_mtime >= started - 1]
    pool = fresh or candidates
    return max(pool, key=lambda p: p.stat().st_mtime)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description='SVG 可视化编辑器本地后端服务',
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        '--projects-root', default='projects',
        help='projects 目录路径(相对仓库根或绝对路径),默认 projects',
    )
    parser.add_argument('--port', type=int, default=5060, help='监听端口,默认 5060')
    parser.add_argument('--host', default='127.0.0.1', help='监听地址,默认 127.0.0.1')
    parser.add_argument('--no-browser', action='store_true', help='启动后不自动打开浏览器')
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    projects_root = Path(args.projects_root)
    if not projects_root.is_absolute():
        projects_root = (_REPO_ROOT / projects_root).resolve()
    if not projects_root.exists():
        print(f'[警告] projects 目录不存在: {projects_root}(将继续启动,列表为空)')

    app = create_app(projects_root)
    url = f'http://{args.host}:{args.port}'
    print(f'[启动] SVG 可视化编辑器后端: {url}')
    print(f'[项目根] {projects_root}')

    if not args.no_browser:
        # 延迟开浏览器,确保服务已就绪。
        threading.Timer(0.8, lambda: webbrowser.open(url)).start()

    app.run(host=args.host, port=args.port, debug=False, threaded=True)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
