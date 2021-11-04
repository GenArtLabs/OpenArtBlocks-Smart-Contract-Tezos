def run_tests_pause(config):
    scenario = sp.test_scenario()

    admin, [alice, bob] = get_addresses()

    config.max_editions = 10000
    c1 = FA2(config=config,
             metadata=sp.utils.metadata_of_url("https://example.com"),
             admin=admin.address)

    scenario.h1("Tests pause")
    scenario.table_of_contents()

    scenario += c1

    scenario.h2("Mint without pause")
    minted = c1.mint(1).run(sender=alice, amount=sp.mutez(1000000))
    scenario.verify(c1.data.ledger[0] == alice.address)

    scenario.h2("Pause")

    scenario.h3("Activation")
    c1.set_pause(True).run(sender=admin, valid=True)

    scenario.h3("Mint not possible")
    c1.mint(1).run(sender=alice, amount=sp.mutez(1000000), valid=False)
    c1.mint(1).run(sender=admin, amount=sp.mutez(1000000), valid=False)

    scenario.h2("Pause activation while pause is already active")

    scenario.h3("Over-activation")
    c1.set_pause(True).run(sender=admin, valid=True)

    scenario.h3("Mint still not possible")
    c1.mint(1).run(sender=alice, amount=sp.mutez(1000000), valid=False)

    scenario.h2("Pause de-activation")
    c1.set_pause(False).run(sender=admin, valid=True)

    scenario.h3("Mint possible again")
    c1.mint(1).run(sender=alice, amount=sp.mutez(1000000), valid=True)
    c1.mint(1).run(sender=admin, amount=sp.mutez(1000000), valid=True)

    scenario.h2("Pause from non-admin")
    c1.set_pause(True).run(sender=alice, valid=False)

    scenario.h2("Pause deactivation from non-admin")
    c1.set_pause(True).run(sender=admin, valid=True)
    c1.set_pause(False).run(sender=alice, valid=False)

    scenario.h2("Behaviour when all token minted (kinda useless)")
    config.max_editions = 0  # Go out of tokens
    c2 = FA2(config=config,
             metadata=sp.utils.metadata_of_url("https://example.com"),
             admin=admin.address)

    scenario += c2

    c2.mint(1).run(sender=alice, amount=sp.mutez(1000000), valid=False)

    scenario.h3("Activation from admin")
    c2.set_pause(True).run(sender=admin, valid=True)
    c2.mint(1).run(sender=alice, amount=sp.mutez(1000000), valid=False)

    scenario.h3("Deactivation from admin")
    c2.set_pause(False).run(sender=admin, valid=True)

    scenario.h3("Activation from non-admin")
    c2.set_pause(True).run(sender=alice, valid=False)

    scenario.h3("Deactivation from non-admin")
    c2.set_pause(True).run(sender=admin, valid=True)
    c2.set_pause(False).run(sender=alice, valid=False)

    scenario.h2("Behaviour when contract is locked")
    # Reset minted tokens
    config.max_editions = 1000
    c3 = FA2(config=config,
             metadata=sp.utils.metadata_of_url("https://example.com"),
             admin=admin.address)

    scenario += c3

    c3.lock().run(sender=admin, valid=True)

    scenario.h3("Activation from admin")
    c3.set_pause(True).run(sender=admin, valid=True)

    scenario.h3("Mint not possible")
    c3.mint(1).run(sender=alice, amount=sp.mutez(1000000), valid=False)

    scenario.h3("Deactivation from admin")
    c3.set_pause(False).run(sender=admin, valid=True)

    scenario.h3("Mint possible")
    c3.mint(1).run(sender=alice, amount=sp.mutez(1000000))

    scenario.h3("Activation from non-admin")
    c3.set_pause(True).run(sender=alice, valid=False)

    scenario.h3("Deactivation from non-admin")
    c3.set_pause(True).run(sender=admin, valid=True)
    c3.set_pause(False).run(sender=alice, valid=False)
