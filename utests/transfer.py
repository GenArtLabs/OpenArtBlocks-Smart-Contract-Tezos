def run_tests_transfer(config):
    scenario = sp.test_scenario()

    admin, [alice, bob] = get_addresses()

    scenario.h1("Tests transfer")
    scenario.table_of_contents()

    #-----------------------------------------------------
    scenario.h2("Simple transfer")

    possessors = [alice]
    contract = create_new_contract(config, admin, scenario, possessors)

    contract.transfer([
        contract.batch_transfer.item(from_=alice.address,
                               txs=[
                                   sp.record(to_=bob.address,
                                             amount=1,
                                             token_id=0)
                               ])
    ]).run(sender=alice)
    possessors[0] = bob
    ownership_test(scenario, contract, possessors)

    #-----------------------------------------------------
    scenario.h2("Self-transfer")

    possessors = [alice]
    contract = create_new_contract(config, admin, scenario, possessors)

    contract.transfer([
        contract.batch_transfer.item(from_=alice.address,
                               txs=[
                                   sp.record(to_=alice.address,
                                             amount=1,
                                             token_id=0)
                               ])
    ]).run(sender=alice)
    ownership_test(scenario, contract, possessors)

    #-----------------------------------------------------
    scenario.h2("Transfering a token in ammount 0")

    possessors = [alice]
    contract = create_new_contract(config, admin, scenario, possessors)

    contract.transfer([
        contract.batch_transfer.item(from_=alice.address,
                               txs=[
                                   sp.record(to_=bob.address,
                                             amount=0,
                                             token_id=0)
                               ])
    ]).run(sender=alice)
    ownership_test(scenario, contract, possessors)

    #-----------------------------------------------------
    scenario.h2("Transfering another's token in ammount 0")

    possessors = [bob]
    contract = create_new_contract(config, admin, scenario, possessors)

    contract.transfer([
        contract.batch_transfer.item(from_=alice.address,
                               txs=[
                                   sp.record(to_=bob.address,
                                             amount=0,
                                             token_id=0)
                               ])
    ]).run(sender=alice)
    ownership_test(scenario, contract, possessors)

    #-----------------------------------------------------
    scenario.h2("Trying to send a non-existing token in 0 amount")

    contract = create_new_contract(config, admin, scenario, [])

    contract.transfer([
        contract.batch_transfer.item(from_=alice.address,
                               txs=[
                                   sp.record(to_=bob.address,
                                             amount=0,
                                             token_id=1000)
                               ])
    ]).run(sender=alice, valid=False)

    #-----------------------------------------------------
    scenario.h2("Sending a token with amount > 1")

    possessors = [alice]
    contract = create_new_contract(config, admin, scenario, possessors)

    scenario.h4("Alice tries to send twice its token (amount) to someone")
    contract.transfer([
        contract.batch_transfer.item(from_=alice.address,
                               txs=[
                                   sp.record(to_=bob.address,
                                             amount=2,
                                             token_id=0)
                               ])
    ]).run(sender=alice, valid=False)
    ownership_test(scenario, contract, possessors)

    #-----------------------------------------------------
    scenario.h2("Sending a token with amount > 1 to itself")

    possessors = [alice]
    contract = create_new_contract(config, admin, scenario, possessors)

    contract.transfer([
        contract.batch_transfer.item(from_=alice.address,
                               txs=[
                                   sp.record(to_=alice.address,
                                             amount=2,
                                             token_id=0)
                               ])
    ]).run(sender=alice, valid=False)
    ownership_test(scenario, contract, possessors)

    #-----------------------------------------------------
    scenario.h2("Sending not-owned token to someone")

    possessors = [bob]
    contract = create_new_contract(config, admin, scenario, possessors)

    contract.transfer([
        contract.batch_transfer.item(from_=alice.address,
                               txs=[
                                   sp.record(to_=bob.address,
                                             amount=1,
                                             token_id=0)
                               ])
    ]).run(sender=alice, valid=False)
    ownership_test(scenario, contract, possessors)

    #-----------------------------------------------------
    scenario.h2("Stealing someone's token")

    possessors = [bob]
    contract = create_new_contract(config, admin, scenario, possessors)

    contract.transfer([
        contract.batch_transfer.item(from_=bob.address,
                               txs=[
                                   sp.record(to_=alice.address,
                                             amount=1,
                                             token_id=0)
                               ])
    ]).run(sender=alice, valid=False)
    ownership_test(scenario, contract, possessors)

    #-----------------------------------------------------
    scenario.h2("Transfering a non-existing token")

    contract = create_new_contract(config, admin, scenario, [])

    contract.transfer([
        contract.batch_transfer.item(from_=alice.address,
                               txs=[
                                   sp.record(to_=bob.address,
                                             amount=1,
                                             token_id=1000)
                               ])
    ]).run(sender=alice, valid=False)

    #-----------------------------------------------------
    scenario.h2("Self-transfering a non-existing token")

    contract = create_new_contract(config, admin, scenario, [])

    contract.transfer([
        contract.batch_transfer.item(from_=alice.address,
                               txs=[
                                   sp.record(to_=alice.address,
                                             amount=1,
                                             token_id=1000)
                               ])
    ]).run(sender=alice, valid=False)

    #-----------------------------------------------------
    scenario.h2("Stealing a non-existing token")

    contract = create_new_contract(config, admin, scenario, [])

    contract.transfer([
        contract.batch_transfer.item(from_=bob.address,
                               txs=[
                                   sp.record(to_=alice.address,
                                             amount=1,
                                             token_id=1000)
                               ])
    ]).run(sender=alice, valid=False)

    #-----------------------------------------------------
    scenario.h2("Admin cannot steal token")

    contract = create_new_contract(config, admin, scenario, [alice])

    contract.transfer([
        contract.batch_transfer.item(from_=alice.address,
                               txs=[
                                   sp.record(to_=admin.address,
                                             amount=1,
                                             token_id=1)
                               ])
    ]).run(sender=admin, valid=False)
    ownership_test(scenario, contract, [alice])

    #-----------------------------------------------------
    scenario.h2("Admin cannot force transfers")

    contract = create_new_contract(config, admin, scenario, [alice])

    contract.transfer([
        contract.batch_transfer.item(from_=alice.address,
                               txs=[
                                   sp.record(to_=bob.address,
                                             amount=1,
                                             token_id=1)
                               ])
    ]).run(sender=admin, valid=False)
    ownership_test(scenario, contract, [alice])

    #-----------------------------------------------------
    scenario.h2("Admin cannot transfer a non-existing token")

    contract = create_new_contract(config, admin, scenario, [])

    contract.transfer([
        contract.batch_transfer.item(from_=admin.address,
                               txs=[
                                   sp.record(to_=bob.address,
                                             amount=1,
                                             token_id=1000)
                               ])
    ]).run(sender=alice, valid=False)

    #-----------------------------------------------------
    scenario.h2("Admin cannot transfer a non-existing token")

    contract = create_new_contract(config, admin, scenario, [])

    contract.transfer([
        contract.batch_transfer.item(from_=admin.address,
                               txs=[
                                   sp.record(to_=admin.address,
                                             amount=1,
                                             token_id=1000)
                               ])
    ]).run(sender=alice, valid=False)

    #-----------------------------------------------------
    scenario.h2("Admin cannot steal a non-existing token")

    contract = create_new_contract(config, admin, scenario, [])

    contract.transfer([
        contract.batch_transfer.item(from_=alice.address,
                               txs=[
                                   sp.record(to_=admin.address,
                                             amount=1,
                                             token_id=1000)
                               ])
    ]).run(sender=alice, valid=False)
