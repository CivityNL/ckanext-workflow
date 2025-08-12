from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, func, select
from sqlalchemy.orm import sessionmaker, relationship, foreign, remote
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.sql import and_

Base = declarative_base()

class Message(Base):
    __tablename__ = 'messages'
    id = Column(Integer, primary_key=True)
    content = Column(String)
    reference_id = Column(Integer, ForeignKey('messages.id'), nullable=True)

    replies = relationship("Message", primaryjoin=foreign(id) == remote(reference_id), uselist=True)
    parent = relationship("Message", primaryjoin=foreign(reference_id) == remote(id), uselist=False)

    @hybrid_property
    def num_replies(self):
        return len(self.replies)

    @num_replies.expression
    def num_replies(cls):
        return (
            select([func.count(Message.id)])
            .select_from(Message)
            .where(Message.reference_id == cls.id)
            .correlate(cls)
            .as_scalar()
        )


# Set up in-memory SQLite and create the table
engine = create_engine('sqlite:///:memory:')
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
session = Session()

# Add sample messages
msg1 = Message(content='Main message')
msg2 = Message(content='Reply 1', parent=msg1)
msg3 = Message(content='Reply 2', parent=msg1)
msg4 = Message(content='Another message')

print([msg1, msg2, msg3, msg4])
session.add_all([msg1, msg2, msg3, msg4])
session.commit()

print(Message.num_replies)
print(Message.num_replies.expression())

# Query ordered by num_replies
results = session.query(Message).order_by(Message.num_replies.desc()).all()
for msg in results:
    print(f"Message ID: {msg.id}, Content: {msg.content}, Replies: {msg.num_replies}")