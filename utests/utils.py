def create_new_contract(config, admin, scenario, ledgers):
    contract = FA2(config=config, 
    metadata=sp.utils.metadata_of_url("https://example.com"),
    admin=admin.address)

    scenario += contract

    for i in range(len(ledgers)):
        contract.mint(1).run(sender=ledgers[i], amount=sp.mutez(1000000))

    return contract

def get_addresses():
    # sp.test_account generates ED25519 key-pairs deterministically:
    admin = sp.test_account("Administrator")
    alice = sp.test_account("Alice")
    bob   = sp.test_account("Robert")
    return admin, [alice, bob]

def ownership_test(scenario, contract, ledgers, quiet=False):
    if not quiet:
        scenario.p("Tokens ownership test")
    for i in range(len(ledgers)):
        scenario.verify(contract.data.ledger[i] == ledgers[i].address)

def set_and_test_base_uri(stringUrl, scenario, contract, sender, valid = True):
    url = sp.bytes('0x' + ''.join([hex(ord(c))[2:] for c in stringUrl]))
    contract.set_base_uri(url).run(sender = sender, valid = valid)
    expectedUri = sp.bytes('0x' + ''.join([hex(ord(c))[2:] for c in stringUrl + '0']))
    resultingUri = contract.token_metadata(0).token_info['']
    if (valid):
        scenario.verify(resultingUri == expectedUri)
    else:
        scenario.verify(resultingUri != expectedUri)

def set_and_test_script(newScript, scenario, contract, sender, valid = True):
    contract.set_script(newScript).run(sender = sender, valid = valid)
    resultingScript = contract.data.script
    if (valid):
        scenario.verify(resultingScript == newScript)
    else:
        scenario.verify(resultingScript != newScript)
