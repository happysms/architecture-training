from datetime import date, timedelta
import pytest
from chap5.adapters import repository
from chap5.domain import model
from chap5.service_layer import services

today = date.today()
tomorrow = today + timedelta(days=1)
later = tomorrow + timedelta(days=10)


class FakeRepository(repository.AbstractRepository):
    def __init__(self, batches):
        self._batches = set(batches)

    def add(self, batch):
        self._batches.add(batch)

    def get(self, reference):
        return next(b for b in self._batches if b.reference == reference)

    def list(self):
        return list(self._batches)


class FakeSession:
    committed = False

    def commit(self):
        self.committed = True


def test_returns_allocation():
    batch = model.Batch("batch1", "Coplicated-lamp", 100, eta=None)
    repo = FakeRepository([batch])

    result = services.allocate("o1", "Coplicated-lamp", 10, repo, FakeSession())
    assert result == "batch1"


def test_add_batch():
    repo, session = FakeSession([]), FakeSession()
    services.add_batch("b1", "Crunchy-armchair", 100, None, repo, session)
    assert repo.get("b1") is not None
    assert session.committed


def test_allocate_returns_allocation():
    repo, session = FakeRepository([]), FakeSession()
    services.add_batch("batch1", "COMPLICATED-LAMP", 100, None, repo, session)
    result = services.allocate("o1", "COMPLICATED-LAMP", 10, repo, session)
    assert result == "batch1"


def test_allocate_errors_for_invalid_sku():
    repo, session = FakeRepository([]), FakeSession()
    services.add_batch("b1", "AREALSKU", 100, None, repo, session)

    with pytest.raises(services.InvalidSku, match="Invalid sku NONEXISTENTSKU"):
        services.allocate("o1", "NONEXISTENTSKU", 10, repo, FakeSession())



# 도메인 계층 테스트
# def test_prefers_current_stock_batches_to_shipments():
#     in_stock_batch = Batch("in_stock_batch", "RETRO-CLOCK", 100, eta=None)
#     shipment_batch = Batch("shipment-batch", "RETRO-CLOCK", 100, eta=tomorrow)
#     line = OrderLine("oref", "RETRO-CLOCK", 10)
#     allocate(line, [in_stock_batch, shipment_batch])
#
#     assert in_stock_batch.available_quantity == 90
#     assert shipment_batch.available_quantity == 100
#
#
# # 서비스 계층 테스트
# def test_prefers_warehouse_batches_to_shipments():
#     in_stock_batch = Batch("in-stock-batch", "RETRO-CLOCK", 100, eta=None)
#     shipment_batch = Batch("shipment-batch", "RETRO-CLOCK", 100, eta=tomorrow)
#     repo = FakeRepository([in_stock_batch, shipment_batch])
#     session = FakeSession()
#     line = OrderLine('oref', "RETRO-CLOCK", 10)
#     services.allocate(line, repo, session)
#
#     assert in_stock_batch.available_quantity == 90
#     assert shipment_batch.available_quantity == 100
