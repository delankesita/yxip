from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import base64
import os
from urllib.parse import urlparse, parse_qs
from typing import Any, Dict, Tuple, Optional

from . import core


def _parse_body(req: BaseHTTPRequestHandler) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    try:
        length = int(req.headers.get('Content-Length', 0))
    except Exception:
        length = 0
    if length <= 0:
        return None, None
    data = req.rfile.read(length)
    try:
        payload = json.loads(data.decode('utf-8'))
        return payload, None
    except Exception as e:
        return None, f"Invalid JSON: {e}"


def _send_json(res: BaseHTTPRequestHandler, status: int, payload: Any) -> None:
    body = json.dumps(payload, ensure_ascii=False).encode('utf-8')
    res.send_response(status)
    res.send_header('Content-Type', 'application/json; charset=utf-8')
    res.send_header('Content-Length', str(len(body)))
    res.end_headers()
    res.wfile.write(body)


class AdminHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        path = parsed.path.rstrip('/')
        qs = parse_qs(parsed.query)

        if path == '/admin/products':
            products = core.list_products()
            _send_json(self, 200, products)
            return
        if path.startswith('/admin/products/'):
            try:
                pid = int(path.split('/')[-1])
                product = core.get_product(pid)
                if product:
                    _send_json(self, 200, product)
                else:
                    _send_json(self, 404, {"error": "Not found"})
            except Exception:
                _send_json(self, 400, {"error": "Invalid product id"})
            return

        if path == '/admin/orders':
            status = qs.get('status', [None])[0]
            start_ts = qs.get('start', [None])[0]
            end_ts = qs.get('end', [None])[0]
            try:
                start_ts_i = int(start_ts) if start_ts else None
                end_ts_i = int(end_ts) if end_ts else None
            except Exception:
                start_ts_i = None
                end_ts_i = None
            orders = core.list_orders(status=status, start_ts=start_ts_i, end_ts=end_ts_i)
            _send_json(self, 200, orders)
            return
        if path.startswith('/admin/orders/'):
            # only support GET by id
            try:
                oid = int(path.split('/')[-1])
                order = core.get_order(oid)
                if order:
                    _send_json(self, 200, order)
                else:
                    _send_json(self, 404, {"error": "Not found"})
            except Exception:
                _send_json(self, 400, {"error": "Invalid order id"})
            return

        if path == '/admin/resources/files':
            records = core.list_files()
            _send_json(self, 200, records)
            return

        if path == '/admin/code-pool':
            status = qs.get('status', [None])[0]
            codes = core.list_codes(status=status)
            _send_json(self, 200, codes)
            return

        if path == '/admin/courses':
            courses = core.list_courses()
            _send_json(self, 200, courses)
            return
        if path == '/admin/chapters':
            course_id = qs.get('course_id', [None])[0]
            try:
                cid = int(course_id) if course_id else None
            except Exception:
                cid = None
            chapters = core.list_chapters(course_id=cid)
            _send_json(self, 200, chapters)
            return

        if path == '/admin/announcements':
            t = qs.get('type', [None])[0]
            items = core.list_announcements(_type=t)
            _send_json(self, 200, items)
            return

        if path == '/admin/dashboard/metrics':
            days = qs.get('days', [None])[0]
            try:
                d = int(days) if days else 30
            except Exception:
                d = 30
            metrics = core.dashboard_metrics(days=d)
            _send_json(self, 200, metrics)
            return

        _send_json(self, 404, {"error": "Not found"})

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        path = parsed.path.rstrip('/')
        payload, err = _parse_body(self)
        if err:
            _send_json(self, 400, {"error": err})
            return
        payload = payload or {}

        if path == '/admin/products':
            try:
                p = core.create_product(
                    name=str(payload.get('name', '')),
                    description=str(payload.get('description', '')),
                    prices=payload.get('prices') or [],
                    metadata=payload.get('metadata') or {},
                )
                _send_json(self, 201, p)
            except Exception as e:
                _send_json(self, 400, {"error": str(e)})
            return

        if path.startswith('/admin/products/') and path.endswith('/delete'):
            try:
                pid = int(path.split('/')[-2])
            except Exception:
                _send_json(self, 400, {"error": "Invalid product id"})
                return
            ok = core.delete_product(pid)
            if ok:
                _send_json(self, 200, {"deleted": True})
            else:
                _send_json(self, 404, {"error": "Not found"})
            return

        if path == '/admin/orders':
            try:
                o = core.create_order(
                    product_id=int(payload.get('product_id')),
                    quantity=int(payload.get('quantity', 1)),
                    amount=payload.get('amount'),
                    currency=str(payload.get('currency', 'CNY')),
                    notes=str(payload.get('notes', '')),
                    metadata=payload.get('metadata') or {},
                )
                _send_json(self, 201, o)
            except Exception as e:
                _send_json(self, 400, {"error": str(e)})
            return

        if path.startswith('/admin/orders/') and path.endswith('/status'):
            try:
                oid = int(path.split('/')[-2])
                status = str(payload.get('status'))
            except Exception:
                _send_json(self, 400, {"error": "Invalid input"})
                return
            updated = core.update_order_status(oid, status)
            if updated:
                _send_json(self, 200, updated)
            else:
                _send_json(self, 404, {"error": "Not found"})
            return

        if path.startswith('/admin/orders/') and path.endswith('/fulfill'):
            try:
                oid = int(path.split('/')[-2])
                note = str(payload.get('note', ''))
            except Exception:
                _send_json(self, 400, {"error": "Invalid input"})
                return
            updated = core.fulfill_order(oid, note=note)
            if updated:
                _send_json(self, 200, updated)
            else:
                _send_json(self, 404, {"error": "Not found"})
            return

        if path.startswith('/admin/orders/') and path.endswith('/refund'):
            try:
                oid = int(path.split('/')[-2])
                reason = str(payload.get('reason', ''))
            except Exception:
                _send_json(self, 400, {"error": "Invalid input"})
                return
            updated = core.refund_order(oid, reason=reason)
            if updated:
                _send_json(self, 200, updated)
            else:
                _send_json(self, 404, {"error": "Not found"})
            return

        if path.startswith('/admin/orders/') and path.endswith('/void'):
            try:
                oid = int(path.split('/')[-2])
                reason = str(payload.get('reason', ''))
            except Exception:
                _send_json(self, 400, {"error": "Invalid input"})
                return
            updated = core.void_order(oid, reason=reason)
            if updated:
                _send_json(self, 200, updated)
            else:
                _send_json(self, 404, {"error": "Not found"})
            return

        if path == '/admin/resources/files':
            # Accept JSON: { filename, content_base64, content_type?, metadata? }
            try:
                filename = str(payload.get('filename'))
                content_b64 = str(payload.get('content_base64'))
            except Exception:
                _send_json(self, 400, {"error": "filename and content_base64 required"})
                return
            try:
                binary = base64.b64decode(content_b64)
            except Exception as e:
                _send_json(self, 400, {"error": f"Invalid base64: {e}"})
                return
            out_path = os.path.join(core.UPLOADS_DIR, filename)
            # prevent directory traversal
            out_path = os.path.abspath(out_path)
            if not out_path.startswith(os.path.abspath(core.UPLOADS_DIR)):
                _send_json(self, 400, {"error": "Invalid filename"})
                return
            with open(out_path, 'wb') as f:
                f.write(binary)
            rec = core.save_file_record(
                filename=filename,
                path=out_path,
                size=len(binary),
                content_type=str(payload.get('content_type') or 'application/octet-stream'),
                metadata=payload.get('metadata') or {},
            )
            _send_json(self, 201, rec)
            return

        if path == '/admin/code-pool':
            codes = payload.get('codes') or []
            if not isinstance(codes, list):
                _send_json(self, 400, {"error": "codes must be a list"})
                return
            result = core.add_codes([str(c) for c in codes])
            _send_json(self, 201, result)
            return

        if path == '/admin/courses':
            title = str(payload.get('title', ''))
            description = str(payload.get('description', ''))
            course = core.create_course(title=title, description=description)
            _send_json(self, 201, course)
            return

        if path == '/admin/chapters':
            try:
                course_id = int(payload.get('course_id'))
            except Exception:
                _send_json(self, 400, {"error": "course_id required"})
                return
            title = str(payload.get('title', ''))
            content = str(payload.get('content', ''))
            order_index = payload.get('order_index')
            try:
                if order_index is not None:
                    order_index = int(order_index)
            except Exception:
                order_index = None
            ch = core.add_chapter(course_id=course_id, title=title, content=content, order_index=order_index)
            _send_json(self, 201, ch)
            return

        if path == '/admin/announcements':
            title = str(payload.get('title', ''))
            content = str(payload.get('content', ''))
            t = str(payload.get('type', 'announcement'))
            a = core.create_announcement(title=title, content=content, _type=t)
            _send_json(self, 201, a)
            return

        if path == '/admin/export':
            data = core.export_all()
            _send_json(self, 200, data)
            return

        if path == '/admin/import':
            try:
                core.import_all(payload)
                _send_json(self, 200, {"ok": True})
            except Exception as e:
                _send_json(self, 400, {"error": str(e)})
            return

        _send_json(self, 404, {"error": "Not found"})

    def do_PUT(self) -> None:
        parsed = urlparse(self.path)
        path = parsed.path.rstrip('/')
        payload, err = _parse_body(self)
        if err:
            _send_json(self, 400, {"error": err})
            return
        payload = payload or {}

        if path.startswith('/admin/products/'):
            try:
                pid = int(path.split('/')[-1])
            except Exception:
                _send_json(self, 400, {"error": "Invalid product id"})
                return
            updated = core.update_product(pid, **payload)
            if updated:
                _send_json(self, 200, updated)
            else:
                _send_json(self, 404, {"error": "Not found"})
            return

        if path.startswith('/admin/courses/'):
            try:
                cid = int(path.split('/')[-1])
            except Exception:
                _send_json(self, 400, {"error": "Invalid course id"})
                return
            updated = core.update_course(cid, **payload)
            if updated:
                _send_json(self, 200, updated)
            else:
                _send_json(self, 404, {"error": "Not found"})
            return

        if path.startswith('/admin/chapters/'):
            try:
                ch_id = int(path.split('/')[-1])
            except Exception:
                _send_json(self, 400, {"error": "Invalid chapter id"})
                return
            updated = core.update_chapter(ch_id, **payload)
            if updated:
                _send_json(self, 200, updated)
            else:
                _send_json(self, 404, {"error": "Not found"})
            return

        if path.startswith('/admin/announcements/'):
            try:
                aid = int(path.split('/')[-1])
            except Exception:
                _send_json(self, 400, {"error": "Invalid announcement id"})
                return
            updated = core.update_announcement(aid, **payload)
            if updated:
                _send_json(self, 200, updated)
            else:
                _send_json(self, 404, {"error": "Not found"})
            return

        _send_json(self, 404, {"error": "Not found"})

    def do_DELETE(self) -> None:
        parsed = urlparse(self.path)
        path = parsed.path.rstrip('/')

        if path.startswith('/admin/products/'):
            try:
                pid = int(path.split('/')[-1])
            except Exception:
                _send_json(self, 400, {"error": "Invalid product id"})
                return
            ok = core.delete_product(pid)
            if ok:
                _send_json(self, 200, {"deleted": True})
            else:
                _send_json(self, 404, {"error": "Not found"})
            return

        if path.startswith('/admin/courses/'):
            try:
                cid = int(path.split('/')[-1])
            except Exception:
                _send_json(self, 400, {"error": "Invalid course id"})
                return
            ok = core.delete_course(cid)
            if ok:
                _send_json(self, 200, {"deleted": True})
            else:
                _send_json(self, 404, {"error": "Not found"})
            return

        if path.startswith('/admin/chapters/'):
            try:
                ch_id = int(path.split('/')[-1])
            except Exception:
                _send_json(self, 400, {"error": "Invalid chapter id"})
                return
            ok = core.delete_chapter(ch_id)
            if ok:
                _send_json(self, 200, {"deleted": True})
            else:
                _send_json(self, 404, {"error": "Not found"})
            return

        if path.startswith('/admin/announcements/'):
            try:
                aid = int(path.split('/')[-1])
            except Exception:
                _send_json(self, 400, {"error": "Invalid announcement id"})
                return
            ok = core.delete_announcement(aid)
            if ok:
                _send_json(self, 200, {"deleted": True})
            else:
                _send_json(self, 404, {"error": "Not found"})
            return

        _send_json(self, 404, {"error": "Not found"})


def run(host: str = '127.0.0.1', port: int = 8787):
    server = HTTPServer((host, port), AdminHandler)
    print(f"Admin server running at http://{host}:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == '__main__':
    run()
