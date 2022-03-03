# architecture-traning
Architecture Patterns with Python (TDD, DDD, EDM)


# Chapter 5. 높은 기어비와 낮은 기어비의 TDD

## 5.2 도메인 계층 테스트를 서비스 계층으로 옮겨야 하는가?

- 도메인 계층 테스트
```python
def test_prefers_current_stock_batches_to_shipments():
    in_stock_batch = Batch("in_stock_batch", "RETRO-CLOCK", 100, eta=None)
    shipment_batch = Batch("shipment-batch", "RETRO-CLOCK", 100, eta=tomorrow)
    line = OrderLine("oref", "RETRO-CLOCK", 10)
    allocate(line, [in_stock_batch, shipment_batch])

    assert in_stock_batch.available_quantity == 90
    assert shipment_batch.available_quantity == 100
```

- 서비스 계층 테스트
```python
def test_prefers_warehouse_batches_to_shipments():
    in_stock_batch = Batch("in-stock-batch", "RETRO-CLOCK", 100, eta=None)
    shipment_batch = Batch("shipment-batch", "RETRO-CLOCK", 100, eta=tomorrow)
    repo = FakeRepository([in_stock_batch, shipment_batch])
    session = FakeSession()
    line = OrderLine('oref', "RETRO-CLOCK", 10)
    services.allocate(line, repo, session)

    assert in_stock_batch.available_quantity == 90
    assert shipment_batch.available_quantity == 100
```


> 왜 도메인 계층의 테스트가 아닌 서비스 계층 테스트로 해야할까?
1. 시스템을 바꾸는 데 어렵지 않다. 
2. 서비스 계층은 시스템을 다양한 방식으로 조정할 수 있는 API를 형성한다.


## 5.5 서비스 계층 테스트를 도메인으로부터 완전히 분리하기
- 서비스 테스트에는 도메인 모델에 대한 의존성이 있다. 테스트 데이터를 설정하고 서비스 계층 함수를 호출하기 위해 도메인 객체를 사용하기 때문이다.
- API를 원시 타입만 사용하도록 다시 작성한다.
- 
```python
# 이전 allocate는 도메인 객체를 받았다.
def allocate(line: OrderLine, repoL AbstractRepository, session) -> str:

# 도메인 의존성을 줄이기 위해 문자열과 정수를 받는다.  -> 원시 타입만 사용!
def allocate(orderid: str, sku: str, qty: int, repo:AbstractRepository, session) -> str:
```



- ex) 직접 Batch 객체를 인스턴스화하므로 여전히 도메인에 의존하고 있다. **나중에 Batch 모델의 동작을 변경하면 수많은 테스트를 변경해야하기에 적합하지 않다.**
```python
def test_returns_allocation():
    batch = model.Batch("batch1", "Coplicated-lamp", 100, eta=None)
    repo = FakeRepository([batch])
    
    result = services.allocate("o1", "Coplicated-lamp", 10, repo, FakeSession())
    assert result == "batch1"
```

###5.5.1 위 예시에 대한 해결책 - 마이그레이션: 모든 도메인 의존성을 픽스처 함수에 넣기
- FakeRepository에 팩토리 함수를 추가하여 추상화를 달성하는 방법 => 도메인 의존성을 한 군데로 모을 수 있다.
```python
class FakeRepository(set):
    @staticmethod
    def for_batch(ref, sku, qty, eta=None):
        return FakeRepository([
            model.Batch(ref, sku, qty, eta)
        ])

    ...
    def test_returns_allocation(self):
        repo = FakeRepository.for_batch("batch1", "Complicated-lamp", 100, eta=None)
        result = services.allocate("o1", "Complicated-lamp", 10, repo, FakeSession())
        
        assert result == "batch1"
```

###5.5.2 예시 해결책: 누락된 서비스 추가
- 재고를 추가하는 서비스가 있다면 이 서비스를 사용해 온전히 서비스 계층의 공식적인 유스 케이스만 사용하는 서비스 계층 테스트를 작성할 수 있다. 

> tip: 일반적으로 서비스 계층 테스트에서 도메인 계층에 있는 요소가 필요하다면 이는 서비스 계층이 완전하지 않다는 사실이다.

```python
def test_add_batch():
    repo, session = FakeSession([]), FakeSession()
    services.add_batch("b1", "Crunchy-armchair", 100, None, repo, session)
    assert repo.get("b1") is not None
    assert session.committed
```


#### 서비스만 사용하는 서비스 테스트 example code
- 서비스 계층 테스트가 오직 서비스 계층에만 의존하기 때문에 얼마든지 필요에 따라 모델을 리팩터링할 수 있다.
```python
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
```

## 5.6 E2E 테스트에 도달할 때까지 계속 개선하기
- 서비스 함수 덕에 엔드포인트를 추가하는 것이 쉬워졌다 JSON을 약간 조작하고 함수를 한 번 호출하면 된다.
```python
@app.route("/add_batch", methods=['POST'])
def add_batch():
    session = get_session()
    repo = repository.SqlAlchemyRepository(session)
    eta = request.json["eta"]

    if eta is not None:
        eta = datetime.fromisoformat(eta).date()
        
    # JSON 조작 함수 한번 호출
    services.add_batch(
        request.json["ref"],
        request.json["sku"],
        request.json["qty"],
        eta,
        repo,
        session,
    )
    return "OK", 201


@app.route("/allocate", methods=["POST"])
def allocate_endpoint():
    session = get_session()
    repo = repository.SqlAlchemyRepository(session)
    try:
        # JSON 조작 함수 한번 호출
        batchref = services.allocate(
            request.json["orderid"],
            request.json["sku"],
            request.json["qty"],
            repo,
            session,
        )
    except (model.OutOfStock, services.InvalidSku) as e:
        return {"message": str(e)}, 400

    return {"batchref": batchref}, 201
```

## 정리: 여러 유형의 테스트를 작성하는 간단한 규칙
- 특성당 엔드투엔드 테스트를 하나씩 만든다는 목표를 세워야 한다.
    - 예를 들어 이런 테스트는 HTTP API를 사용할 가능성이 높다. 목표는 어떤 특성이 잘 작동하는지 보고 움직이는 모든 부품이 서로 잘 연결되어 움직이는지 살펴보는 것이다.


- 테스트 대부분은 서비스 계층을 만드는 걸 권한다.
  - 이런 테스트는 커버리지, 실행 시간, 효율 사이를 잘 절충할 수 있게 해준다. 각 테스트는 어떤 기능의 한 경로를 테스트하고 I/O에 가짜 객체를 사용하는 경향이 있다. 이 테스트는 모든 에지 케이스를 다루고, 비즈니스 로직의 모든 입력과 출력을 테스트해볼 수 있는 좋은 장소다.


- 도메인 모델을 사용하는 핵심 테스트를 적게 작성하고 유지하는 걸 권한다.
  - 이런 테스트는 좀 더 커버리지가 작고(좁은 범위를 테스트), 더 깨지기 쉽다. 하지만 이런 테스트가 제공하는 피드백이 가장 크다. 이런 테스트를 나중에 서비스 계층 기반 테스트로 대신할 수 있다면 테스트를 주저하지 말고 삭제하는 것을 권한다.


- 오류 처리도 특성으로 취급하자.
  - 이상적인 경우 애플리케이션은 모든 오류가 진입점(예: 플라스크)으로 거슬러 올라와서 처리되는 구조로 되어 있다. 단지 각 기능의 정상 경로만 테스트하고 모든 비정상 경로를 테스트하는 엔드투엔드 테스트를 하나만 유지하면 된다는 의미다(물론 비정상 경로를 테스트하는 단위 테스트가 많이 있어야 한다.).
  
