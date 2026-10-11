# Right before payout: verify policy signature, invoice hash snapshot, payee, amount,
# budget and nonce. If anything is wrong, return failures and do NOT call PayPal.
# See build guide section 8.5.
