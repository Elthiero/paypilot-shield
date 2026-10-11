# Signed policy (mandate) helpers.
# Server builds the exact payload string, the browser signs it, the server verifies.
# WebCrypto returns raw 64 byte r||s signatures, Python needs DER (encode_dss_signature).
# See build guide section 8.3 for the full code.
