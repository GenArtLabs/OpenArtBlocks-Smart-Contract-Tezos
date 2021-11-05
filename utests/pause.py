def run_tests_pause(config):
    scenario = sp.test_scenario()

    admin, [alice, bob] = get_addresses()

    config.max_editions = 10000

    scenario.h1("Tests pause")
    scenario.table_of_contents()

    #-----------------------------------------------------
    scenario.h2("Pause activation")

    contract = create_new_contract(config, admin, scenario, [])

    contract.set_pause(True).run(sender=admin)

    #-----------------------------------------------------
    scenario.h2("Pause activation by non-admin")

    contract = create_new_contract(config, admin, scenario, [])

    contract.set_pause(True).run(sender=alice, valid=False)

    #-----------------------------------------------------
    scenario.h2("Mint after pause not possible")

    possessors = [alice]
    contract = create_new_contract(config, admin, scenario, possessors)

    scenario.h3("Mint without pause")
    minted = contract.mint(1).run(sender=alice, amount=sp.mutez(1000000))
    scenario.verify(contract.data.ledger[0] == alice.address)

    contract.set_pause(True).run(sender=admin)

    scenario.h3("Mint after pause")

    scenario.p("From standard wallet")
    contract.mint(1).run(sender=alice, amount=sp.mutez(1000000), valid=False)

    scenario.p("From admin")
    contract.mint(1).run(sender=admin, amount=sp.mutez(1000000), valid=False)

    #-----------------------------------------------------
    scenario.h2("Pause activation while pause is already active")

    contract = create_new_contract(config, admin, scenario, [])

    contract.set_pause(True).run(sender=admin)

    scenario.h3("Over-activation")

    contract.set_pause(True).run(sender=admin)

    scenario.h3("Mint still not possible")
    contract.mint(1).run(sender=alice, amount=sp.mutez(1000000), valid=False)

    #-----------------------------------------------------
    scenario.h2("Mint after pause de-activation")

    contract = create_new_contract(config, admin, scenario, [])

    contract.set_pause(True).run(sender=admin)

    contract.set_pause(False).run(sender=admin)

    scenario.h3("Mint possible again")
    contract.mint(1).run(sender=alice, amount=sp.mutez(1000000))
    contract.mint(1).run(sender=admin, amount=sp.mutez(1000000))

    #-----------------------------------------------------
    scenario.h2("Pause deactivation from non-admin")

    contract = create_new_contract(config, admin, scenario, [])

    contract.set_pause(True).run(sender=admin)

    contract.set_pause(False).run(sender=alice, valid=False)

    #-----------------------------------------------------
    scenario.h2("Behaviour when all token minted")
    config.max_editions = 0  # Go out of tokens

    contract = create_new_contract(config, admin, scenario, [])

    scenario.h3("No pause, cannot mint")
    contract.mint(1).run(sender=alice, amount=sp.mutez(1000000), valid=False)

    scenario.h3("Pause activation by admin, cannot mint")
    contract.set_pause(True).run(sender=admin)
    contract.mint(1).run(sender=alice, amount=sp.mutez(1000000), valid=False)

    scenario.h3("Pause deactivation from admin, cannot mint")
    contract.set_pause(False).run(sender=admin)
    contract.mint(1).run(sender=alice, amount=sp.mutez(1000000), valid=False)

    scenario.h3("Activation from non-admin")
    contract.set_pause(True).run(sender=alice, valid=False)

    scenario.h3("Deactivation from non-admin")
    contract.set_pause(True).run(sender=admin)
    contract.set_pause(False).run(sender=alice, valid=False)

    #-----------------------------------------------------
    scenario.h2("Behaviour when contract is locked")
    # Reset minted tokens
    config.max_editions = 1000

    contract = create_new_contract(config, admin, scenario, [])

    contract.lock().run(sender=admin)

    scenario.h3("No pause, mint possible")
    contract.mint(1).run(sender=alice, amount=sp.mutez(1000000))

    scenario.h3("Pause activation from admin, cannot mint")
    contract.set_pause(True).run(sender=admin)
    contract.mint(1).run(sender=alice, amount=sp.mutez(1000000), valid=False)

    scenario.h3("Pause deactivation from admin, mint possible")
    contract.set_pause(False).run(sender=admin)
    contract.mint(1).run(sender=alice, amount=sp.mutez(1000000))

    scenario.h3("Activation from non-admin")
    contract.set_pause(True).run(sender=alice, valid=False)

    scenario.h3("Deactivation from non-admin")
    contract.set_pause(True).run(sender=admin)
    contract.set_pause(False).run(sender=alice, valid=False)
