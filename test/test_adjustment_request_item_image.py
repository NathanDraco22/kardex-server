from kardex.repos.v1.adjustment_requests import AdjustmentRequestItem


def _build_item(**overrides: object) -> AdjustmentRequestItem:
    data: dict[str, object] = {
        "productId": "product-1",
        "productName": "Producto de prueba",
        "countedQuantity": 1,
        "cost": 100,
        "systemStock": 2,
        "difference": -1,
        "subtotal": 100,
    }
    data.update(overrides)
    return AdjustmentRequestItem.model_validate(data)


def test_adjustment_request_item_serializes_image() -> None:
    item = _build_item(image="https://example.com/producto.jpg")

    assert item.image == "https://example.com/producto.jpg"
    assert item.model_dump()["image"] == "https://example.com/producto.jpg"


def test_adjustment_request_item_defaults_image_for_legacy_documents() -> None:
    item = _build_item()

    assert item.image == ""
    assert item.model_dump()["image"] == ""
