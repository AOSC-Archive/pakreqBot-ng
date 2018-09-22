async def test_index(cli, tables_and_data):
    response = await cli.get('/')
    assert response.status == 200