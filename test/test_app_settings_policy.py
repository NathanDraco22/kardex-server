import pytest

from kardex.core.policies import AppSettingsPolicy, ConvertedOrderShiftPolicy
from kardex.repos.v1.app_settings import AppSettingInDb


def _settings(**overrides: object) -> AppSettingInDb:
    data: dict[str, object] = {"id": "Default", "createdAt": 0}
    data.update(overrides)
    return AppSettingInDb.model_validate(data)


@pytest.mark.parametrize(
    ("use_shifts", "charge_to_shift", "require_shift", "expected"),
    [
        (False, False, False, ConvertedOrderShiftPolicy.NEVER),
        (False, False, True, ConvertedOrderShiftPolicy.NEVER),
        (False, True, False, ConvertedOrderShiftPolicy.NEVER),
        (False, True, True, ConvertedOrderShiftPolicy.NEVER),
        (True, False, False, ConvertedOrderShiftPolicy.NEVER),
        (True, False, True, ConvertedOrderShiftPolicy.NEVER),
        (True, True, False, ConvertedOrderShiftPolicy.OPTIONAL),
        (True, True, True, ConvertedOrderShiftPolicy.REQUIRED),
    ],
)
def test_converted_order_shift_policy_truth_table(
    use_shifts: bool,
    charge_to_shift: bool,
    require_shift: bool,
    expected: ConvertedOrderShiftPolicy,
):
    settings = _settings(
        useShifts=use_shifts,
        chargeConvertedOrdersToShift=charge_to_shift,
        requireShiftForConvertedOrders=require_shift,
    )

    policy = AppSettingsPolicy(settings)

    assert policy.converted_order_shift_policy is expected


@pytest.mark.parametrize(
    ("shift_policy", "links_to_shift", "requires_open_shift"),
    [
        (ConvertedOrderShiftPolicy.NEVER, False, False),
        (ConvertedOrderShiftPolicy.OPTIONAL, True, False),
        (ConvertedOrderShiftPolicy.REQUIRED, True, True),
    ],
)
def test_converted_order_shift_policy_derived_flags(
    shift_policy: ConvertedOrderShiftPolicy,
    links_to_shift: bool,
    requires_open_shift: bool,
):
    assert shift_policy.links_to_shift is links_to_shift
    assert shift_policy.requires_open_shift is requires_open_shift


@pytest.mark.parametrize("round_up", [False, True])
def test_round_up_invoice_totals(round_up: bool):
    policy = AppSettingsPolicy(_settings(roundUpInvoiceTotals=round_up))

    assert policy.round_up_invoice_totals is round_up


@pytest.mark.parametrize("allow_outside_shift", [False, True])
def test_allows_cancellations_outside_shift(allow_outside_shift: bool):
    policy = AppSettingsPolicy(
        _settings(allowCancellationsOutsideShift=allow_outside_shift)
    )

    assert policy.allows_cancellations_outside_shift is allow_outside_shift


def test_missing_settings_uses_conservative_defaults():
    policy = AppSettingsPolicy(None)

    assert policy.converted_order_shift_policy is ConvertedOrderShiftPolicy.NEVER
    assert policy.round_up_invoice_totals is False
    assert policy.allows_cancellations_outside_shift is False
