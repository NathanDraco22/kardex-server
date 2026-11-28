import kardex.core.policies as policies

EXPECTED_MODULES = {
    "AppSettingsPolicy": (
        "kardex.core.policies.app_settings.app_settings_policy"
    ),
    "CancellationDecision": (
        "kardex.core.policies.decisions.cancellation_decision"
    ),
    "ConvertedOrderShiftPolicy": (
        "kardex.core.policies.app_settings.app_settings_policy"
    ),
    "CreditNotePolicy": "kardex.core.policies.credit_notes.credit_note_policy",
    "DevolutionPolicy": "kardex.core.policies.devolutions.devolution_policy",
    "InvoiceCancellationPolicy": (
        "kardex.core.policies.invoices.invoice_cancellation_policy"
    ),
    "InvoiceRoundingPolicy": (
        "kardex.core.policies.invoices.invoice_rounding_policy"
    ),
    "PolicyDecision": "kardex.core.policies.decisions.policy_decision",
    "ReceiptApplicationPolicy": (
        "kardex.core.policies.receipts.receipt_application_policy"
    ),
    "ReceiptCancellationPolicy": (
        "kardex.core.policies.receipts.receipt_cancellation_policy"
    ),
    "ReceiptPaymentDecision": (
        "kardex.core.policies.receipts.receipt_payment_policy"
    ),
    "ReceiptPaymentPolicy": (
        "kardex.core.policies.receipts.receipt_payment_policy"
    ),
}


def test_public_api_exports_all_policies_and_decisions():
    assert set(policies.__all__) == set(EXPECTED_MODULES)

    for name, module in EXPECTED_MODULES.items():
        exported = getattr(policies, name)
        assert exported.__module__ == module
