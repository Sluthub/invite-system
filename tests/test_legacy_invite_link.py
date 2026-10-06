def test_existing_sluthub_invite_links_redirect_to_current_flow(client):
    response = client.get("/i/ABCDEF")
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/j/ABCDEF")
