def run_tests_multi_transfer(config):
    scenario = sp.test_scenario()

    admin, [alice, bob] = get_addresses()

    scenario.h1("Tests multiple transfer")
    scenario.table_of_contents()

    #-----------------------------------------------------
    scenario.h2("Simple transfer")

    possessors = [alice]*2
    contract = create_new_contract(config, admin, scenario, possessors)

    contract.transfer([
        contract.batch_transfer.item(from_=alice.address,
                               txs=[
                                   sp.record(to_=bob.address,
                                             amount=1,
                                             token_id=0)
                               ,
                                   sp.record(to_=bob.address,
                                             amount=1,
                                             token_id=1)
                               ])
    ]).run(sender=alice)
    possessors[0] = bob
    possessors[1] = bob
    ownership_test(scenario, contract, possessors)

    #-----------------------------------------------------
    scenario.h2("Sending 2 times the same token to itself")

    possessors = [alice]
    contract = create_new_contract(config, admin, scenario, possessors)

    contract.transfer([
        contract.batch_transfer.item(from_=alice.address,
                               txs=[
                                   sp.record(to_=alice.address,
                                             amount=1,
                                             token_id=0)
                               ,
                                   sp.record(to_=alice.address,
                                             amount=1,
                                             token_id=0)
                               ])
    ]).run(sender=alice)
    ownership_test(scenario, contract, possessors)

    #-----------------------------------------------------
    scenario.h2("Sending 2 different tokens to 2 different addresses")

    possessors = [alice]*2
    contract = create_new_contract(config, admin, scenario, possessors)

    contract.transfer([
        contract.batch_transfer.item(from_=alice.address,
                               txs=[
                                   sp.record(to_=bob.address,
                                             amount=1,
                                             token_id=0)
                               ,
                                   sp.record(to_=admin.address,
                                             amount=1,
                                             token_id=1)
                               ])
    ]).run(sender=alice)
    possessors[0] = bob
    possessors[1] = admin
    ownership_test(scenario, contract, possessors)

    #-----------------------------------------------------
    scenario.h2("Sending 1 token to someone else and 2 times the same token to itself")

    possessors = [alice]*2
    contract = create_new_contract(config, admin, scenario, possessors)

    contract.transfer([
        contract.batch_transfer.item(from_=alice.address,
                               txs=[
                                   sp.record(to_=bob.address,
                                             amount=1,
                                             token_id=1)
                               ,
                                   sp.record(to_=alice.address,
                                             amount=1,
                                             token_id=0)
                               ,
                                   sp.record(to_=alice.address,
                                             amount=1,
                                             token_id=0)
                               ])
    ]).run(sender=alice)
    possessors[1] = bob
    ownership_test(scenario, contract, possessors)

    #-----------------------------------------------------
    scenario.h2("Sending the same token to itself and (then) someone else")

    possessors = [alice]
    contract = create_new_contract(config, admin, scenario, possessors)

    contract.transfer([
        contract.batch_transfer.item(from_=alice.address,
                               txs=[
                                   sp.record(to_=alice.address,
                                             amount=1,
                                             token_id=0)
                               ,
                                   sp.record(to_=bob.address,
                                             amount=1,
                                             token_id=0)
                               ])
    ]).run(sender=alice)
    possessors[0] = bob
    ownership_test(scenario, contract, possessors)

    #-----------------------------------------------------
    scenario.h2("Sending the same token to someone else and (then) itself")

    possessors = [alice]
    contract = create_new_contract(config, admin, scenario, possessors)

    contract.transfer([
        contract.batch_transfer.item(from_=alice.address,
                               txs=[
                                   sp.record(to_=bob.address,
                                             amount=1,
                                             token_id=0)
                               ,
                                   sp.record(to_=alice.address,
                                             amount=1,
                                             token_id=0)
                               ])
    ]).run(sender=alice, valid=False)

    scenario.p("Transaction has been cancelled")
    ownership_test(scenario, contract, possessors)

    #-----------------------------------------------------
    scenario.h2("Sending one existing token and 1 non-existing token")

    possessors = [alice]
    contract = create_new_contract(config, admin, scenario, possessors)

    contract.transfer([
        contract.batch_transfer.item(from_=alice.address,
                               txs=[
                                   sp.record(to_=bob.address,
                                             amount=1,
                                             token_id=0)
                               ,
                                   sp.record(to_=bob.address,
                                             amount=1,
                                             token_id=1000)
                               ])
    ]).run(sender=alice, valid=False)

    scenario.p("Transaction has been cancelled")
    ownership_test(scenario, contract, possessors)

    #-----------------------------------------------------
    scenario.h2("Sending 2 non-existing tokens to someone")

    contract = create_new_contract(config, admin, scenario, [])

    contract.transfer([
        contract.batch_transfer.item(from_=alice.address,
                               txs=[
                                   sp.record(to_=bob.address,
                                             amount=1,
                                             token_id=1000)
                               ,
                                   sp.record(to_=bob.address,
                                             amount=1,
                                             token_id=1001)
                               ])
    ]).run(sender=alice, valid=False)

    #-----------------------------------------------------
    scenario.h2("Sending 2 times the same token to someone")

    possessors = [alice]
    contract = create_new_contract(config, admin, scenario, possessors)

    contract.transfer([
        contract.batch_transfer.item(from_=alice.address,
                               txs=[
                                   sp.record(to_=bob.address,
                                             amount=1,
                                             token_id=0)
                               ,
                                   sp.record(to_=bob.address,
                                             amount=1,
                                             token_id=0)
                               ])
    ]).run(sender=alice, valid=False)

    scenario.p("Transaction has been cancelled")
    ownership_test(scenario, contract, possessors)

    #-----------------------------------------------------
    scenario.h2("Sending the same token to 2 different addresses")

    possessors = [alice]
    contract = create_new_contract(config, admin, scenario, possessors)

    contract.transfer([
        contract.batch_transfer.item(from_=alice.address,
                               txs=[
                                   sp.record(to_=bob.address,
                                             amount=1,
                                             token_id=0)
                               ,
                                   sp.record(to_=admin.address,
                                             amount=1,
                                             token_id=0)
                               ])
    ]).run(sender=alice, valid=False)

    scenario.p("Transaction has been cancelled")
    ownership_test(scenario, contract, possessors)

    #-----------------------------------------------------
    scenario.h2("Cannot force a transaction between two addresses")

    contract = create_new_contract(config, admin, scenario, [bob]*2)

    contract.transfer([
        contract.batch_transfer.item(from_=bob.address,
                               txs=[
                                   sp.record(to_=admin.address,
                                             amount=1,
                                             token_id=0)
                               ,
                                   sp.record(to_=alice.address,
                                             amount=1,
                                             token_id=1)
                               ])
    ]).run(sender=alice, valid=False)

