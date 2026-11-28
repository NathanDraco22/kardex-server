from kardex.repos.v1.app_settings.models.app_setting_model import (
    AppSettingInDb,
    CreateAppSetting,
    UpdateAppSetting,
)


def test_abono_received_amount_defaults_false():
    settings = CreateAppSetting()
    assert settings.useAbonoReceivedAmount is False


def test_legacy_app_setting_without_abono_received_amount_defaults_false():
    legacy_doc = {
        "id": "Default",
        "createdAt": 1700000000000,
        "currency": "NIO",
    }
    settings = AppSettingInDb.model_validate(legacy_doc)
    assert settings.useAbonoReceivedAmount is False


def test_update_abono_received_amount_is_partial():
    patch = UpdateAppSetting(useAbonoReceivedAmount=True)
    assert patch.model_dump(exclude_unset=True) == {
        "useAbonoReceivedAmount": True,
    }


def test_abono_received_amount_serializes_in_settings():
    settings = AppSettingInDb(
        id="Default",
        createdAt=1700000000000,
        useAbonoReceivedAmount=True,
    )
    payload = settings.model_dump()
    assert payload["useAbonoReceivedAmount"] is True
