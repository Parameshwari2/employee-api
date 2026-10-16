from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Employee


def get_all_reports(db: Session, manager_id: int) -> list[Employee]:
    tree = (
        select(Employee.id)
        .where(Employee.manager_id == manager_id)
        .cte("tree", recursive=True)
    )
    # UNION (not UNION ALL) also protects against accidental loops
    tree = tree.union(select(Employee.id).join(tree, Employee.manager_id == tree.c.id))
    return list(db.scalars(select(Employee).where(Employee.id.in_(select(tree.c.id)))))