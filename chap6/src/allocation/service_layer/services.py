from __future__ import annotations
from typing import Optional
from datetime import date
from chap6.src.allocation.domain import model
from allocation.domain.model import OrderLine
from allocation.service_layer import unit_of_work

from chap6.src.allocation.service_layer.unit_of_work import AbstractUnitOfWork


class InvalidSku(Exception):
    pass


def is_valid_sku(sku, batches):
    return sku in {b.sku for b in batches}


def add_batch(
        ref: str, sku: str, qty: int, eta: Optional[date],
        uow: unit_of_work.AbstractUnitOfWork,
    ):
    with uow:
        uow.batches.add(model.Batch(ref, sku, qty, eta))
        uow.commit()


def allocate(orderid: str, sku: str, qty: int, uow: unit_of_work.AbstractUnitOfWork) -> str:
    line = OrderLine(orderid, sku, qty)

    with uow:  # 콘텍스트 관리자로 UoW를 시작한다.  => 영속적 저장소에 대한 단일 진입점 -> 어떤 객체가 메모리에 적재됐고 어떤 객체가 최종 상태인지를 기억한다.
        batches = uow.batches.list()  # uow.batches는 배치 저장소다. 따라서 UoW는 영속적 저장소에 대한 접근을 제공한다.

        if not is_valid_sku(line.sku, batches):
            raise InvalidSku('Invalid sku {line.sku}')

        batchref = model.allocate(line, batches)
        uow.commit()  # 작업이 끝나면 UoW를 사용해 커밋하거나 롤백한다.

    return batchref


def reallocate(line: OrderLine, uow: unit_of_work.AbtractUnitOfWork) -> str:
    with uow:
        batch = uow.batches.get(sku=line.sku)
        if batch is None:
            raise InvalidSku('Invalid sku {line.sku}')

        # 실제로 Uow에 예외 커밋 조건을 설정하여 실패했을 경우 커밋이 진행되지 않는다.
        batch.deallocate(line)  # deallocate() 가 실패하면 당연히 allocate()를 호출하는 걸 원치 않는다.
        allocate(line)  # 실제로 allocate()가 실패한다면 deallocate()한 결과만 커밋하고 싶지는 않을것이다.
        uow.commit()


def change_batch_quantity(batchref: str, new_qty: int, uow: AbstractUnitOfWork):
    with uow:
        batch = uow.batches.get(reference=batchref)
        batch.change_purchased_quantity(new_qty)
        while batch.available_quantity < 0:
            line = batch.deallocate_one()
        uow.commit()




