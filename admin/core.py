import json
import os
import time
from typing import Any, Dict, List, Optional, Tuple

# Simple file-based persistence layer for an admin backend.
# This module avoids external dependencies and focuses on providing
# CRUD helpers for products, orders, resources, courses/chapters,
# announcements/FAQ, code pool, and simple dashboard metrics.

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
UPLOADS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads")

os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(UPLOADS_DIR, exist_ok=True)


def _data_path(name: str) -> str:
    return os.path.join(DATA_DIR, f"{name}.json")


def _read_json(path: str, default: Any) -> Any:
    if not os.path.exists(path):
        return default
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default


def _write_json(path: str, data: Any) -> None:
    tmp_path = f"{path}.tmp"
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(tmp_path, path)


def _now_ts() -> int:
    return int(time.time())


# ------------------------------
# Products and Prices
# ------------------------------

def list_products() -> List[Dict[str, Any]]:
    return _read_json(_data_path("products"), [])


def _next_id(items: List[Dict[str, Any]]) -> int:
    return (max((i.get("id", 0) for i in items), default=0) + 1) if items else 1


def create_product(name: str, description: str = "", prices: Optional[List[Dict[str, Any]]] = None,
                   metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    products = list_products()
    pid = _next_id(products)
    product = {
        "id": pid,
        "name": name,
        "description": description,  # rich text (HTML) supported as string
        "prices": prices or [],      # [{type: 'one_time'|'subscription', amount: int cents, currency: str, interval?: 'day'|'week'|'month'|'year'}]
        "metadata": metadata or {},
        "created_at": _now_ts(),
        "updated_at": _now_ts(),
    }
    products.append(product)
    _write_json(_data_path("products"), products)
    return product


def get_product(product_id: int) -> Optional[Dict[str, Any]]:
    for p in list_products():
        if p.get("id") == product_id:
            return p
    return None


def update_product(product_id: int, **updates: Any) -> Optional[Dict[str, Any]]:
    products = list_products()
    found = None
    for p in products:
        if p.get("id") == product_id:
            for k, v in updates.items():
                if k in {"name", "description", "prices", "metadata"}:
                    p[k] = v
            p["updated_at"] = _now_ts()
            found = p
            break
    if found is not None:
        _write_json(_data_path("products"), products)
    return found


def delete_product(product_id: int) -> bool:
    products = list_products()
    new_list = [p for p in products if p.get("id") != product_id]
    if len(new_list) != len(products):
        _write_json(_data_path("products"), new_list)
        return True
    return False


# ------------------------------
# Orders and Payments
# ------------------------------

def list_orders(status: Optional[str] = None, start_ts: Optional[int] = None, end_ts: Optional[int] = None) -> List[Dict[str, Any]]:
    orders = _read_json(_data_path("orders"), [])
    result = []
    for o in orders:
        if status and o.get("status") != status:
            continue
        ts = o.get("created_at", 0)
        if start_ts and ts < start_ts:
            continue
        if end_ts and ts > end_ts:
            continue
        result.append(o)
    return result


def create_order(product_id: int, quantity: int = 1, amount: Optional[int] = None, currency: str = "CNY",
                 notes: str = "", metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    orders = _read_json(_data_path("orders"), [])
    products = list_products()
    product = next((p for p in products if p.get("id") == product_id), None)
    if product is None:
        raise ValueError("Product not found")

    if amount is None:
        # If no explicit amount, try the first price definition.
        first_price = (product.get("prices") or [{}])[0]
        amount = int(first_price.get("amount") or 0)
        currency = first_price.get("currency") or currency

    oid = _next_id(orders)
    order = {
        "id": oid,
        "product_id": product_id,
        "quantity": int(quantity or 1),
        "amount": int(amount),
        "currency": currency,
        "status": "pending",  # pending -> paid -> fulfilled / refunded / voided
        "notes": notes,
        "metadata": metadata or {},
        "created_at": _now_ts(),
        "updated_at": _now_ts(),
    }
    orders.append(order)
    _write_json(_data_path("orders"), orders)
    return order


def get_order(order_id: int) -> Optional[Dict[str, Any]]:
    for o in _read_json(_data_path("orders"), []):
        if o.get("id") == order_id:
            return o
    return None


def update_order_status(order_id: int, status: str) -> Optional[Dict[str, Any]]:
    assert status in {"pending", "paid", "fulfilled", "refunded", "voided"}
    orders = _read_json(_data_path("orders"), [])
    found = None
    for o in orders:
        if o.get("id") == order_id:
            o["status"] = status
            o["updated_at"] = _now_ts()
            found = o
            break
    if found is not None:
        _write_json(_data_path("orders"), orders)
    return found


def fulfill_order(order_id: int, note: str = "") -> Optional[Dict[str, Any]]:
    # Manual fulfillment: mark as fulfilled and (optionally) assign resources from code pool if any.
    order = get_order(order_id)
    if not order:
        return None
    # simulate resource assignment from code pool
    assigned_codes: List[str] = []
    try:
        pool = _read_json(_data_path("code_pool"), [])
    except Exception:
        pool = []
    for item in pool:
        if item.get("status") == "available" and len(assigned_codes) < order.get("quantity", 1):
            item["status"] = "assigned"
            item["assigned_to_order_id"] = order_id
            assigned_codes.append(item.get("code"))
    _write_json(_data_path("code_pool"), pool)

    updated = update_order_status(order_id, "fulfilled")
    if updated is not None:
        updated.setdefault("fulfillment", {})
        updated["fulfillment"]["note"] = note
        updated["fulfillment"]["assigned_codes"] = assigned_codes
        orders = _read_json(_data_path("orders"), [])
        for i, o in enumerate(orders):
            if o.get("id") == order_id:
                orders[i] = updated
                break
        _write_json(_data_path("orders"), orders)
    return updated


def refund_order(order_id: int, reason: str = "") -> Optional[Dict[str, Any]]:
    updated = update_order_status(order_id, "refunded")
    if updated is not None:
        updated.setdefault("refund", {})
        updated["refund"]["reason"] = reason
        orders = _read_json(_data_path("orders"), [])
        for i, o in enumerate(orders):
            if o.get("id") == order_id:
                orders[i] = updated
                break
        _write_json(_data_path("orders"), orders)
    return updated


def void_order(order_id: int, reason: str = "") -> Optional[Dict[str, Any]]:
    updated = update_order_status(order_id, "voided")
    if updated is not None:
        updated.setdefault("void", {})
        updated["void"]["reason"] = reason
        orders = _read_json(_data_path("orders"), [])
        for i, o in enumerate(orders):
            if o.get("id") == order_id:
                orders[i] = updated
                break
        _write_json(_data_path("orders"), orders)
    return updated


# ------------------------------
# Resources: files, code pool
# ------------------------------

def list_files() -> List[Dict[str, Any]]:
    return _read_json(_data_path("files"), [])


def save_file_record(filename: str, path: str, size: int, content_type: str = "application/octet-stream",
                     metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    records = list_files()
    rid = _next_id(records)
    record = {
        "id": rid,
        "filename": filename,
        "path": path,
        "size": size,
        "content_type": content_type,
        "metadata": metadata or {},
        "created_at": _now_ts(),
    }
    records.append(record)
    _write_json(_data_path("files"), records)
    return record


def list_codes(status: Optional[str] = None) -> List[Dict[str, Any]]:
    pool = _read_json(_data_path("code_pool"), [])
    if status:
        return [c for c in pool if c.get("status") == status]
    return pool


def add_codes(codes: List[str]) -> Dict[str, Any]:
    pool = _read_json(_data_path("code_pool"), [])
    existing = {c.get("code") for c in pool}
    added = []
    for code in codes:
        if code in existing:
            continue
        pool.append({
            "id": _next_id(pool),
            "code": code,
            "status": "available",
            "assigned_to_order_id": None,
            "created_at": _now_ts(),
        })
        added.append(code)
    _write_json(_data_path("code_pool"), pool)
    return {"added": added, "total": len(pool)}


def mark_code_used(code: str) -> bool:
    pool = _read_json(_data_path("code_pool"), [])
    changed = False
    for item in pool:
        if item.get("code") == code:
            item["status"] = "used"
            changed = True
            break
    if changed:
        _write_json(_data_path("code_pool"), pool)
    return changed


# ------------------------------
# Courses and Chapters
# ------------------------------

def list_courses() -> List[Dict[str, Any]]:
    return _read_json(_data_path("courses"), [])


def create_course(title: str, description: str = "") -> Dict[str, Any]:
    courses = list_courses()
    cid = _next_id(courses)
    course = {
        "id": cid,
        "title": title,
        "description": description,  # rich text allowed
        "created_at": _now_ts(),
        "updated_at": _now_ts(),
    }
    courses.append(course)
    _write_json(_data_path("courses"), courses)
    return course


def update_course(course_id: int, **updates: Any) -> Optional[Dict[str, Any]]:
    courses = list_courses()
    found = None
    for c in courses:
        if c.get("id") == course_id:
            for k, v in updates.items():
                if k in {"title", "description"}:
                    c[k] = v
            c["updated_at"] = _now_ts()
            found = c
            break
    if found is not None:
        _write_json(_data_path("courses"), courses)
    return found


def delete_course(course_id: int) -> bool:
    courses = list_courses()
    new_list = [c for c in courses if c.get("id") != course_id]
    if len(new_list) != len(courses):
        _write_json(_data_path("courses"), new_list)
        # remove chapters under this course
        chapters = list_chapters(course_id)
        if chapters:
            rest = [ch for ch in _read_json(_data_path("chapters"), []) if ch.get("course_id") != course_id]
            _write_json(_data_path("chapters"), rest)
        return True
    return False


def list_chapters(course_id: Optional[int] = None) -> List[Dict[str, Any]]:
    all_chapters = _read_json(_data_path("chapters"), [])
    if course_id is None:
        return all_chapters
    return [ch for ch in all_chapters if ch.get("course_id") == course_id]


def add_chapter(course_id: int, title: str, content: str = "", order_index: Optional[int] = None) -> Dict[str, Any]:
    chapters = _read_json(_data_path("chapters"), [])
    cid = _next_id(chapters)
    if order_index is None:
        # order_index defaults to append position
        order_index = max((ch.get("order_index", 0) for ch in chapters if ch.get("course_id") == course_id), default=0) + 1
    chapter = {
        "id": cid,
        "course_id": course_id,
        "title": title,
        "content": content,  # rich text allowed
        "order_index": order_index,
        "created_at": _now_ts(),
        "updated_at": _now_ts(),
    }
    chapters.append(chapter)
    _write_json(_data_path("chapters"), chapters)
    return chapter


def update_chapter(chapter_id: int, **updates: Any) -> Optional[Dict[str, Any]]:
    chapters = _read_json(_data_path("chapters"), [])
    found = None
    for ch in chapters:
        if ch.get("id") == chapter_id:
            for k, v in updates.items():
                if k in {"title", "content", "order_index"}:
                    ch[k] = v
            ch["updated_at"] = _now_ts()
            found = ch
            break
    if found is not None:
        _write_json(_data_path("chapters"), chapters)
    return found


def delete_chapter(chapter_id: int) -> bool:
    chapters = _read_json(_data_path("chapters"), [])
    new_list = [ch for ch in chapters if ch.get("id") != chapter_id]
    if len(new_list) != len(chapters):
        _write_json(_data_path("chapters"), new_list)
        return True
    return False


# ------------------------------
# Announcements and FAQ
# ------------------------------

def list_announcements(_type: Optional[str] = None) -> List[Dict[str, Any]]:
    items = _read_json(_data_path("announcements"), [])
    if _type:
        return [a for a in items if a.get("type") == _type]
    return items


def create_announcement(title: str, content: str, _type: str = "announcement") -> Dict[str, Any]:
    assert _type in {"announcement", "faq"}
    items = list_announcements()
    aid = _next_id(items)
    item = {
        "id": aid,
        "type": _type,  # announcement | faq
        "title": title,
        "content": content,  # rich text (HTML) allowed
        "created_at": _now_ts(),
        "updated_at": _now_ts(),
    }
    items.append(item)
    _write_json(_data_path("announcements"), items)
    return item


def update_announcement(announcement_id: int, **updates: Any) -> Optional[Dict[str, Any]]:
    items = list_announcements()
    found = None
    for it in items:
        if it.get("id") == announcement_id:
            for k, v in updates.items():
                if k in {"title", "content", "type"}:
                    it[k] = v
            it["updated_at"] = _now_ts()
            found = it
            break
    if found is not None:
        _write_json(_data_path("announcements"), items)
    return found


def delete_announcement(announcement_id: int) -> bool:
    items = list_announcements()
    new_list = [a for a in items if a.get("id") != announcement_id]
    if len(new_list) != len(items):
        _write_json(_data_path("announcements"), new_list)
        return True
    return False


# ------------------------------
# Dashboard Metrics
# ------------------------------

def _group_orders_by_day(orders: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    from datetime import datetime
    groups: Dict[str, List[Dict[str, Any]]] = {}
    for o in orders:
        ts = o.get("created_at", 0)
        day = datetime.utcfromtimestamp(ts).strftime("%Y-%m-%d")
        groups.setdefault(day, []).append(o)
    return groups


def dashboard_metrics(days: int = 30) -> Dict[str, Any]:
    """Compute simple dashboard metrics for the last N days.

    Returns keys:
    - revenue_by_day: [{date, revenue}]
    - orders_by_day: [{date, count}]
    - pending_count
    - abnormal_count (e.g., voided or refunded)
    """
    from datetime import datetime, timedelta

    all_orders = _read_json(_data_path("orders"), [])
    cutoff_ts = int((datetime.utcnow() - timedelta(days=days)).timestamp())
    recent_orders = [o for o in all_orders if o.get("created_at", 0) >= cutoff_ts]
    grouped = _group_orders_by_day(recent_orders)

    revenue_by_day: List[Dict[str, Any]] = []
    orders_by_day: List[Dict[str, Any]] = []

    # Build a complete date range
    for i in range(days, -1, -1):
        d = (datetime.utcnow() - timedelta(days=i)).strftime("%Y-%m-%d")
        day_orders = grouped.get(d, [])
        revenue = 0
        for o in day_orders:
            if o.get("status") in {"paid", "fulfilled"}:
                revenue += int(o.get("amount", 0)) * int(o.get("quantity", 1))
        revenue_by_day.append({"date": d, "revenue": revenue})
        orders_by_day.append({"date": d, "count": len(day_orders)})

    pending_count = len([o for o in all_orders if o.get("status") == "pending"])
    abnormal_count = len([o for o in all_orders if o.get("status") in {"voided", "refunded"}])

    return {
        "revenue_by_day": revenue_by_day,
        "orders_by_day": orders_by_day,
        "pending_count": pending_count,
        "abnormal_count": abnormal_count,
    }


# ------------------------------
# Utility: import/export data
# ------------------------------

def export_all() -> Dict[str, Any]:
    return {
        "products": list_products(),
        "orders": _read_json(_data_path("orders"), []),
        "files": list_files(),
        "code_pool": _read_json(_data_path("code_pool"), []),
        "courses": list_courses(),
        "chapters": _read_json(_data_path("chapters"), []),
        "announcements": list_announcements(),
    }


def import_all(payload: Dict[str, Any]) -> None:
    if not isinstance(payload, dict):
        raise ValueError("payload must be a dict")
    for key in ["products", "orders", "files", "code_pool", "courses", "chapters", "announcements"]:
        if key in payload:
            _write_json(_data_path(key), payload[key])
