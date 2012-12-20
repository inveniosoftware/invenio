"""
WebDeposit database models.
"""

from invenio.sqlalchemyutils import db


class WebDepositDraft(db.Model):
    """Represents a deposition draft."""
    __tablename__ = 'deposition_drafts'
    uuid = db.Column(db.String(36),
                     primary_key=True,
                     unique=True,
                     nullable=False)
    step = db.Column(db.Integer(15,
                         unsigned=True),
                         nullable=False)
    user_id = db.Column(db.Integer(15,
                        unsigned=True),
                        nullable=False)
    form_type = db.Column(db.String(45),
                          nullable=False)
    form_values = db.Column(db.String(2048),
                            nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False)

class WebDepositWorkflow(db.Model):
    """Represents a deposition workflow."""
    __tablename__ = 'deposition_workflows'
    uuid = db.Column(db.String(36),
                     primary_key=True,
                     unique=True,
                     nullable=False)
    dep_type = db.Column(db.String(45),
                     nullable=False)
    current_step = db.Column(db.Integer(15,
                        unsigned=True),
                        nullable=False)
    status = db.Column(db.Binary, nullable=False)

__all__ = ['WebDepositDraft']
