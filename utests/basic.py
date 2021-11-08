def run_basic_test(config):
    scenario = sp.test_scenario()
    scenario.h1("FA2 Contract Name: " + config.name)
    scenario.table_of_contents()

    admin, [alice, bob] = get_addresses()

    config.max_editions = 2

    # Let's display the accounts:
    scenario.h2("Accounts")
    scenario.show([admin, alice, bob])
    c1 = FA2(config=config,
             metadata=sp.utils.metadata_of_url("https://example.com"),
             admin=admin.address)
    scenario += c1

    stringUrl = 'https://yo.com/api/'
    url = sp.bytes('0x' + ''.join([hex(ord(c))[2:] for c in stringUrl]))
    c1.set_base_uri(url).run(sender=admin)

    scenario.h2("Mint")
    minted = c1.mint(1).run(sender=alice, amount=sp.mutez(1000000))
    scenario.verify(c1.data.ledger[0] == alice.address)

    scenario.h2("Set base URI")
    resultingUri = c1.token_metadata(0).token_info['']
    scenario.verify(resultingUri == sp.bytes(
        '0x' + ''.join([hex(ord(c))[2:] for c in stringUrl + '0'])))

    scenario.h2("Fail because of bad price")
    c1.mint(1).run(sender=alice, amount=sp.mutez(2), valid=False)

    scenario.h2("Test ledger")
    c1.mint(1).run(sender=alice, amount=sp.mutez(1000000))
    scenario.verify(c1.data.ledger[0] == alice.address)
    scenario.verify(c1.data.ledger[1] == alice.address)

    scenario.h2("Mint when max number of token reached")
    c1.mint(1).run(sender=alice, amount=sp.mutez(1000000), valid=False)
