from email.policy import default
from sqlalchemy import Column, Integer, create_engine, Boolean
from sqlalchemy.orm import declarative_base, Session


Base = declarative_base()


class Match(Base):
    __tablename__ = 'session'
    id = Column(Integer, primary_key=True)
    completed = Column(Boolean, default=False)
    _1 = Column(Integer, default=0)
    _2 = Column(Integer, default=0)
    _3 = Column(Integer, default=0)
    _4 = Column(Integer, default=0)
    _5 = Column(Integer, default=0)
    _6 = Column(Integer, default=0)
    _7 = Column(Integer, default=0)
    _8 = Column(Integer, default=0)
    _9 = Column(Integer, default=0)

    def __repr__(self):
        return f'{self.id=},\n{self._1}, {self._2}, {self._3},\n{self._4}, {self._5}, {self._6},\n{self._7}, {self._8}, {self._9}'


engine = create_engine('sqlite:///sessions.sqlite', future=True)

Base.metadata.create_all(engine)


def create_session(id):
    with Session(engine) as session:
        match = Match(id=id)
        session.add_all([match])
        session.commit()
        return True


def get_session(id):
    with Session(engine) as session:
        match = session.get(Match, id)
        if match:
            return [match._1, match._2, match._3, match._4, match._5, match._6, match._7, match._8, match._9]
        else:
            return False


def get_session_complete(id):
    with Session(engine) as session:
        match = session.get(Match, id)
        return match.completed


def session_complete(id):
    with Session(engine) as session:
        match = session.get(Match, id)
        match.completed = True
        session.commit()
        return True


def update_session(id, array):
    with Session(engine) as session:
        match = session.get(Match, id)
        match._1, match._2, match._3, match._4, match._5, match._6, match._7, match._8, match._9 = array
        session.commit()
        return True


def delete_session(id):
    with Session(engine) as session:
        session.delete(session.get(Match, id))
        session.commit()
        return True
