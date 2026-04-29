## Summary

Describe the change and why it is useful.

## Safety Impact

Explain whether this affects strategy decisions, firewall checks, execution, config, or docs only.

## Validation

List the commands you ran, for example:

```bash
python3 -m unittest discover -s tests
python3 -m compileall src tests
```

## Checklist

- [ ] This does not frame BaseRoute as an AI trading bot.
- [ ] This does not bypass deterministic strategy or firewall checks.
- [ ] Changes affecting fund movement include focused tests.
- [ ] No secrets, private keys, logs, or local history files are included.
