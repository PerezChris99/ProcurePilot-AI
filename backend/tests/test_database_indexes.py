from sqlalchemy import inspect
from app.core.database import Base, get_db
from app.main import app
from app import models  # noqa: F401 -- import all ORM tables


def test_compound_user_scoped_and_order_audit_indexes_are_declared():
    index_map={
        table.name:{index.name:tuple(column.name for column in index.columns)
                    for index in table.indexes}
        for table in Base.metadata.tables.values()
    }
    assert index_map['procurement_requests']['ix_procurement_requests_user_created']==('user_id','created_at')
    assert index_map['procurement_requests']['ix_procurement_requests_user_status_created']==('user_id','status','created_at')
    assert index_map['purchase_orders']['ix_purchase_orders_user_status_created']==('user_id','status','created_at')
    assert index_map['audit_events']['ix_audit_events_order_created']==('purchase_order_id','created_at')
    assert index_map['audit_events']['ix_audit_events_user_created']==('user_id','created_at')
    assert index_map['approvals']['ix_approvals_po_created']==('purchase_order_id','created_at')


def test_payment_provider_identifiers_are_uniquely_indexed_in_sqlite_test_schema(client):
    # No user data needed: introspect actual created database constraints.
    db_generator=app.dependency_overrides[get_db]()
    db=next(db_generator)
    try:
        indexes=inspect(db.bind).get_indexes('payments')
        ids={item['name']:item for item in indexes}
        assert bool(ids['ix_payments_paypal_order_id']['unique'])
        assert bool(ids['ix_payments_capture_id']['unique'])
    finally:
        db_generator.close()
