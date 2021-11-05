def run_tests_get_balance(config):
    scenario = sp.test_scenario()

    admin, [alice, bob] = get_addresses()

    scenario.h1("Tests get balance")

    scenario.table_of_contents()

    #-----------------------------------------------------
    scenario.h2("Get balance on possessed token")
    contract = create_new_contract(config, admin, scenario, [alice])

    balance = contract.get_balance(
        sp.record(owner=alice.address, token_id=0)
    )
    scenario.verify(balance == 1)

    # #-----------------------------------------------------
    # scenario.h2("Get balance on non-existing token")
    # contract = create_new_contract(config, admin, scenario, [])

    # balance = contract.get_balance(
    #     sp.record(owner=alice.address, token_id=0)
    # )
    # scenario.verify(balance == 0)

    #-----------------------------------------------------
    scenario.h2("Get balance on non-possessed token")
    contract = create_new_contract(config, admin, scenario, [alice])

    balance = contract.get_balance(
        sp.record(owner=bob.address, token_id=0)
    )
    scenario.verify(balance == 0)

    #-----------------------------------------------------
    scenario.h2("Get balance after receiving token")
    contract = create_new_contract(config, admin, scenario, [alice])

    scenario.h3("Token not possessed")
    balance = contract.get_balance(
        sp.record(owner=bob.address, token_id=0)
    )
    scenario.verify(balance == 0)

    scenario.h3("Alice sends the token to Bob")
    contract.transfer([
        contract.batch_transfer.item(from_=alice.address,
                               txs=[
                                   sp.record(to_=bob.address,amount=1,token_id=0)
                               ])
    ]).run(sender=alice)

    scenario.h3("Token is now possessed")
    balance = contract.get_balance(
        sp.record(owner=bob.address, token_id=0)
    )
    scenario.verify(balance == 1)
