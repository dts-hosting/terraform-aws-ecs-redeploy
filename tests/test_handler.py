import redeploy as h


def test_event_tag():
    assert h.parse_event_for_tag({}) == None
    assert h.parse_event_for_tag({'body': '{"push_data": {}}'}) == None
    assert h.parse_event_for_tag({'body': '{"push_data": { "tag": "" }}'}) == None
    assert h.parse_event_for_tag({'body': '{"push_data": { "tag": "latest" }}'}) == "latest"
