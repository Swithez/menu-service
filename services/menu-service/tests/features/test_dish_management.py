"""
Фича: управление блюдами с историей цен.
"""


class TestFeatureDishCreate:
    """Создание блюд."""

    async def test_create_dish_minimal(self, client) -> None:
        payload = {"name": "Borscht", "price": "120.00"}
        resp = await client.post("/api/v1/dishes/", json=payload)
        assert resp.status_code == 201
        body = resp.json()
        assert body["name"] == "Borscht"
        assert body["price"] == "120.00"
        assert body["is_available"] is True

    async def test_create_dish_with_category(self, client) -> None:
        cat_resp = await client.post("/api/v1/categories/", json={"name": "Fish"})
        cat_id = cat_resp.json()["id"]
        resp = await client.post(
            "/api/v1/dishes/", json={"name": "Trout", "price": "650.00", "category_id": cat_id}
        )
        assert resp.status_code == 201
        assert resp.json()["category_id"] == cat_id

    async def test_create_dish_with_invalid_category_returns_404(self, client) -> None:
        fake_cat_id = "00000000-0000-0000-0000-000000000000"
        resp = await client.post(
            "/api/v1/dishes/",
            json={"name": "Orphan Dish", "price": "100.00", "category_id": fake_cat_id},
        )
        assert resp.status_code == 404

    async def test_create_dish_zero_price_returns_422(self, client) -> None:
        resp = await client.post("/api/v1/dishes/", json={"name": "Free", "price": "0"})
        assert resp.status_code == 422

    async def test_create_dish_negative_price_returns_422(self, client) -> None:
        resp = await client.post("/api/v1/dishes/", json={"name": "X", "price": "-50"})
        assert resp.status_code == 422


class TestFeatureDishRead:
    """Чтение и фильтрация блюд."""

    async def test_list_dishes_empty(self, client) -> None:
        resp = await client.get("/api/v1/dishes/")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    async def test_get_dish_by_id(self, client) -> None:
        create_resp = await client.post(
            "/api/v1/dishes/", json={"name": "Pelmeni", "price": "300.00"}
        )
        dish_id = create_resp.json()["id"]
        resp = await client.get(f"/api/v1/dishes/{dish_id}")
        assert resp.status_code == 200
        assert resp.json()["id"] == dish_id

    async def test_get_nonexistent_dish_returns_404(self, client) -> None:
        resp = await client.get("/api/v1/dishes/00000000-0000-0000-0000-000000000000")
        assert resp.status_code == 404

    async def test_filter_by_available_only(self, client) -> None:
        await client.post("/api/v1/dishes/", json={"name": "Available Dish", "price": "100", "is_available": True})
        await client.post("/api/v1/dishes/", json={"name": "Unavailable Dish", "price": "100", "is_available": False})
        resp = await client.get("/api/v1/dishes/?available_only=true")
        names = [d["name"] for d in resp.json()]
        assert "Available Dish" in names
        assert "Unavailable Dish" not in names

    async def test_filter_by_category(self, client) -> None:
        cat_resp = await client.post("/api/v1/categories/", json={"name": "Meat"})
        cat_id = cat_resp.json()["id"]
        await client.post("/api/v1/dishes/", json={"name": "Schnitzel", "price": "700", "category_id": cat_id})
        await client.post("/api/v1/dishes/", json={"name": "Salad", "price": "200"})
        resp = await client.get(f"/api/v1/dishes/?category_id={cat_id}")
        names = [d["name"] for d in resp.json()]
        assert "Schnitzel" in names
        assert "Salad" not in names


class TestFeatureDishUpdate:
    """Обновление данных блюда."""

    async def test_mark_dish_unavailable(self, client) -> None:
        create_resp = await client.post(
            "/api/v1/dishes/", json={"name": "Seasonal Dish", "price": "400.00"}
        )
        dish_id = create_resp.json()["id"]
        resp = await client.patch(f"/api/v1/dishes/{dish_id}", json={"is_available": False})
        assert resp.status_code == 200
        assert resp.json()["is_available"] is False

    async def test_update_dish_name(self, client) -> None:
        create_resp = await client.post(
            "/api/v1/dishes/", json={"name": "Old Name", "price": "200.00"}
        )
        dish_id = create_resp.json()["id"]
        resp = await client.patch(f"/api/v1/dishes/{dish_id}", json={"name": "New Name"})
        assert resp.status_code == 200
        assert resp.json()["name"] == "New Name"


class TestFeaturePriceManagement:
    """Цены с историей изменений."""

    async def test_update_price_stores_history(self, client) -> None:
        create_resp = await client.post(
            "/api/v1/dishes/", json={"name": "Coffee", "price": "150.00"}
        )
        dish_id = create_resp.json()["id"]
        resp = await client.patch(f"/api/v1/dishes/{dish_id}/price", json={"price": "200.00"})
        assert resp.status_code == 200
        assert resp.json()["price"] == "200.00"
        history_resp = await client.get(f"/api/v1/dishes/{dish_id}/price-history")
        assert history_resp.status_code == 200
        history = history_resp.json()
        assert len(history) >= 1
        assert history[0]["old_price"] == "150.00"
        assert history[0]["new_price"] == "200.00"

    async def test_update_price_same_value_no_history(self, client) -> None:
        create_resp = await client.post(
            "/api/v1/dishes/", json={"name": "Tea", "price": "80.00"}
        )
        dish_id = create_resp.json()["id"]
        await client.patch(f"/api/v1/dishes/{dish_id}/price", json={"price": "80.00"})
        history_resp = await client.get(f"/api/v1/dishes/{dish_id}/price-history")
        assert len(history_resp.json()) == 0

    async def test_multiple_price_changes_recorded(self, client) -> None:
        create_resp = await client.post(
            "/api/v1/dishes/", json={"name": "Latte", "price": "200.00"}
        )
        dish_id = create_resp.json()["id"]
        await client.patch(f"/api/v1/dishes/{dish_id}/price", json={"price": "220.00"})
        await client.patch(f"/api/v1/dishes/{dish_id}/price", json={"price": "250.00"})
        history_resp = await client.get(f"/api/v1/dishes/{dish_id}/price-history")
        history = history_resp.json()
        assert len(history) == 2
        new_prices = {h["new_price"] for h in history}
        assert new_prices == {"220.00", "250.00"}


class TestFeatureDishDelete:
    """Удаление блюд."""

    async def test_delete_dish_returns_204(self, client) -> None:
        create_resp = await client.post(
            "/api/v1/dishes/", json={"name": "Temporary Dish", "price": "50.00"}
        )
        dish_id = create_resp.json()["id"]
        resp = await client.delete(f"/api/v1/dishes/{dish_id}")
        assert resp.status_code == 204

    async def test_delete_dish_removes_it(self, client) -> None:
        create_resp = await client.post(
            "/api/v1/dishes/", json={"name": "Gone Dish", "price": "50.00"}
        )
        dish_id = create_resp.json()["id"]
        await client.delete(f"/api/v1/dishes/{dish_id}")
        resp = await client.get(f"/api/v1/dishes/{dish_id}")
        assert resp.status_code == 404


class TestFeatureDishIngredients:
    """Управление ингредиентами блюда."""

    _PRODUCT_ID = "00000000-0000-0000-0000-000000000001"

    async def _create_dish(self, client) -> str:
        resp = await client.post("/api/v1/dishes/", json={"name": "Curry", "price": "350.00"})
        return resp.json()["id"]

    async def _add_ingredient(self, client, dish_id: str, **overrides) -> dict:
        payload = {
            "product_id": self._PRODUCT_ID,
            "product_name": "Chicken",
            "quantity": "0.300",
            "unit": "kg",
            **overrides,
        }
        resp = await client.post(f"/api/v1/dishes/{dish_id}/ingredients", json=payload)
        return resp

    async def test_list_ingredients_empty_on_new_dish(self, client) -> None:
        dish_id = await self._create_dish(client)
        resp = await client.get(f"/api/v1/dishes/{dish_id}/ingredients")
        assert resp.status_code == 200
        assert resp.json() == []

    async def test_add_ingredient_returns_201(self, client) -> None:
        dish_id = await self._create_dish(client)
        resp = await self._add_ingredient(client, dish_id)
        assert resp.status_code == 201
        body = resp.json()
        assert body["product_name"] == "Chicken"
        assert body["unit"] == "kg"
        assert body["dish_id"] == dish_id

    async def test_get_dish_includes_ingredients(self, client) -> None:
        dish_id = await self._create_dish(client)
        await self._add_ingredient(client, dish_id, product_name="Rice")
        resp = await client.get(f"/api/v1/dishes/{dish_id}")
        assert resp.status_code == 200
        ingredients = resp.json()["ingredients"]
        assert len(ingredients) == 1
        assert ingredients[0]["product_name"] == "Rice"

    async def test_delete_ingredient_returns_204(self, client) -> None:
        dish_id = await self._create_dish(client)
        add_resp = await self._add_ingredient(client, dish_id)
        ingredient_id = add_resp.json()["id"]
        resp = await client.delete(f"/api/v1/dishes/{dish_id}/ingredients/{ingredient_id}")
        assert resp.status_code == 204

    async def test_delete_ingredient_removes_it_from_list(self, client) -> None:
        dish_id = await self._create_dish(client)
        add_resp = await self._add_ingredient(client, dish_id)
        ingredient_id = add_resp.json()["id"]
        await client.delete(f"/api/v1/dishes/{dish_id}/ingredients/{ingredient_id}")
        resp = await client.get(f"/api/v1/dishes/{dish_id}/ingredients")
        assert all(i["id"] != ingredient_id for i in resp.json())

    async def test_add_ingredient_zero_quantity_rejected(self, client) -> None:
        dish_id = await self._create_dish(client)
        resp = await self._add_ingredient(client, dish_id, quantity="0")
        assert resp.status_code == 422

    async def test_add_ingredient_to_nonexistent_dish_returns_404(self, client) -> None:
        resp = await client.post(
            "/api/v1/dishes/00000000-0000-0000-0000-000000000000/ingredients",
            json={"product_id": self._PRODUCT_ID, "product_name": "Oil",
                  "quantity": "0.1", "unit": "l"},
        )
        assert resp.status_code == 404

    async def test_delete_dish_cascades_to_ingredients(self, client) -> None:
        dish_id = await self._create_dish(client)
        await self._add_ingredient(client, dish_id)
        await client.delete(f"/api/v1/dishes/{dish_id}")
        resp = await client.get(f"/api/v1/dishes/{dish_id}")
        assert resp.status_code == 404
