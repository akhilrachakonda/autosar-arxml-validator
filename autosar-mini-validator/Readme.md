# AUTOSAR Mini Validator (Demo)

A lightweight Python proof-of-concept to validate AUTOSAR `.arxml` files.

### Rules Implemented
- **DUP_SHORT_NAME** – detects duplicate element names
- **NO_TYPE_TREF** – detects missing type references in `VARIABLE-DATA-PROTOTYPE`
- **COMPU_METHOD_INCOMPLETE** – detects missing `UNIT-REF` or `COMPU-SCALE` in computation methods

### Run
```bash
python validator.py sample.arxml reports