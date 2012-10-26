"""
WebDeposit database models.
"""

from invenio.sqlalchemyutils import db


class WebSubmitDraft(db.Model):
    """Represents a submit draft."""
    __tablename__ = 'submit_drafts'
    draft_id = db.Column(db.Integer(15, unsigned=True),
                   nullable=False,
                   primary_key=True,
                   unique=True,
                   autoincrement=True)
    user_id = db.Column(db.Integer(15, unsigned=True),
                       nullable=False,
                       server_default='0')
    form_type = db.Column(db.String(45), nullable=False)
    form_values = db.Column(db.String(512), nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False)

__all__ = ['WebSubmitDraft']
