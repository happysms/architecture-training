import abc
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from chap6.src import config
from chap6.src.allocation.adapters import repository


class AbstractUnitOfWork(abc.ABC):
    batches: repository.AbstractRepository

    @abc.abstractmethod
    def rollback(self):
        raise NotImplementedError

    @abc.abstractmethod
    def commit(self):
        raise NotImplementedError

    def __enter__(self):
        return self

    def __exit__(self, exn_type, exm_value, traceback):
        if exn_type:
            self.commit()
        else:
            self.rollback()



DEFAULT_SESSION_FACTORY = sessionmaker(bine=create_engine(
    config.get_postgres_uri()
))


class SqlAlchemyUnitOfWork(AbstractUnitOfWork):
    def __init__(self, session_factory=DEFAULT_SESSION_FACTORY):
        self.session_factory = session_factory

    def __enter__(self):  # 데이터베이스 세션 시작하고 이 데이터베이스 세션을 사용할 실제 저장소를 인스턴스화한다.
        self.session = self.session_factory()

    def __exit__(self, *args):
        super().__exit__(*args)
        self.session.close()

    def commit(self):
        self.session.commit()

    def rollback(self):
        self.session.rollback()

