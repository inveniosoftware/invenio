"""
WebDeposit database models.
"""

from invenio.sqlalchemyutils import db


class WebDepositDraft(db.Model):
    """Represents a submit draft."""
    __tablename__ = 'deposition_drafts'
    uuid = db.Column(db.String(36),
                     primary_key=True,
                     unique=True,
                     nullable=False)
    draft_id = db.Column(db.Integer(15,
                         unsigned=True),
                         nullable=True)
    user_id = db.Column(db.Integer(15,
                        unsigned=True),
                        nullable=False)
    dep_type = db.Column(db.String(45),
                         nullable=False)
    form_type = db.Column(db.String(45),
                          nullable=False)
    form_values = db.Column(db.String(2048),
                            nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False)

__all__ = ['WebDepositDraft']
