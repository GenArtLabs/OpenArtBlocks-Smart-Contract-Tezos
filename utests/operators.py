def run_tests_operator(config):
    scenario = sp.test_scenario()

    admin, [alice, bob] = get_addresses()

    config.max_editions = 10000

    scenario.h1("Tests operator")

    scenario.table_of_contents()

    scenario.p("Creates one operator")
    op = sp.test_account("Operator")

    #-----------------------------------------------------
    scenario.h2("Operator tries to transfer Alice's token before being permitted to")

    possessors = [alice]
    contract = create_new_contract(config, admin, scenario, possessors)

    contract.transfer([
        contract.batch_transfer.item(from_=alice.address,
                               txs=[
                                   sp.record(to_=bob.address, amount=1, token_id=0)
                                ])
    ]).run(sender=op, valid=False)
    ownership_test(scenario, contract, possessors)

    #-----------------------------------------------------
    scenario.h2((
        "Alice grants Operator rights on a token\n"
        "Operator sends token to Bob"
    ))

    possessors = [alice]
    contract = create_new_contract(config, admin, scenario, possessors)

    contract.update_operators([
        sp.variant("add_operator", contract.operator_param.make(
            owner=alice.address,
            operator=op.address,
            token_id=0))
    ]).run(sender=alice)

    contract.transfer([
        contract.batch_transfer.item(from_=alice.address,
                               txs=[
                                   sp.record(to_=bob.address,amount=1,token_id=0)
                               ])
    ]).run(sender=op)
    possessors[0] = bob
    ownership_test(scenario, contract, possessors)

    #-----------------------------------------------------
    scenario.h2((
        "Alice grants Operator rights on a token but sends it before operator could"
    ))

    possessors = [alice]
    contract = create_new_contract(config, admin, scenario, possessors)

    contract.update_operators([
        sp.variant("add_operator", contract.operator_param.make(
            owner=alice.address,
            operator=op.address,
            token_id=0))
    ]).run(sender=alice)

    contract.transfer([
        contract.batch_transfer.item(from_=alice.address,
                               txs=[
                                   sp.record(to_=bob.address,amount=1,token_id=0)
                               ])
    ]).run(sender=alice)

    possessors[0] = bob
    ownership_test(scenario, contract, possessors)

    scenario.p("Operator is too late but tries to transfer token to Admin")

    contract.transfer([
        contract.batch_transfer.item(from_=alice.address,
                               txs=[
                                   sp.record(to_=admin.address, amount=1, token_id=0)
                               ])
    ]).run(sender=op, valid=False)
    ownership_test(scenario, contract, possessors)

    #-----------------------------------------------------
    scenario.h2((
        "Operator can use a granted token when it comes back to the owner"
    ))

    possessors = [alice]
    contract = create_new_contract(config, admin, scenario, possessors)

    contract.update_operators([
        sp.variant("add_operator", contract.operator_param.make(
            owner=alice.address,
            operator=op.address,
            token_id=0))
    ]).run(sender=alice)

    scenario.p("Alice sends token to Bob")

    contract.transfer([
        contract.batch_transfer.item(from_=alice.address,
                               txs=[
                                   sp.record(to_=bob.address,amount=1,token_id=0)
                               ])
    ]).run(sender=alice)

    scenario.p("Bob sends token to Alice")

    contract.transfer([
        contract.batch_transfer.item(from_=bob.address,
                               txs=[
                                   sp.record(to_=alice.address,amount=1,token_id=0)
                               ])
    ]).run(sender=bob)

    scenario.p("Operator still can transfer token")

    contract.transfer([
        contract.batch_transfer.item(from_=alice.address,
                               txs=[
                                   sp.record(to_=bob.address, amount=1, token_id=0)
                               ])
    ]).run(sender=op)
    possessors[0] = bob
    ownership_test(scenario, contract, possessors)

    #-----------------------------------------------------
    scenario.h2((
        "Operator has only right on a token for a specific owner"
    ))

    possessors = [alice]
    contract = create_new_contract(config, admin, scenario, possessors)

    scenario.p("Bob gives Operator right to transfer its token 0")

    contract.update_operators([
        sp.variant("add_operator", contract.operator_param.make(
            owner=bob.address,
            operator=op.address,
            token_id=0))
    ]).run(sender=bob)

    scenario.p("Operator cannot transfer token 0 from Alice to Bob")

    contract.transfer([
        contract.batch_transfer.item(from_=alice.address,
                               txs=[
                                   sp.record(to_=bob.address, amount=1, token_id=0)
                               ])
    ]).run(sender=op, valid=False)
    ownership_test(scenario, contract, possessors)

    #-----------------------------------------------------
    scenario.h2("Token loopback does not cancels operator rights")

    possessors = [alice]
    contract = create_new_contract(config, admin, scenario, possessors)

    scenario.p("Alice grants Operator rights on token 0")

    contract.update_operators([
        sp.variant("add_operator", contract.operator_param.make(
            owner=alice.address,
            operator=op.address,
            token_id=0))
    ]).run(sender=alice)

    scenario.p("Alice transfers token 0 to itself")

    contract.transfer([
        contract.batch_transfer.item(from_=alice.address,
                               txs=[
                                   sp.record(to_=alice.address, amount=1, token_id=0)
                               ])
    ]).run(sender=alice)
    ownership_test(scenario, contract, possessors)

    scenario.p("Operator still has rights on Alice's token 0")
    contract.transfer([
        contract.batch_transfer.item(from_=alice.address,
                               txs=[
                                   sp.record(to_=bob.address, amount=1, token_id=0)
                               ])
    ]).run(sender=op)
    possessors[0] = bob
    ownership_test(scenario, contract, possessors)

     #-----------------------------------------------------
    scenario.h2("Token loopback from operator does not cancels operator rights")

    possessors = [alice]
    contract = create_new_contract(config, admin, scenario, possessors)

    scenario.p("Alice grants Operator rights on token 0")

    contract.update_operators([
        sp.variant("add_operator", contract.operator_param.make(
            owner=alice.address,
            operator=op.address,
            token_id=0))
    ]).run(sender=alice)

    scenario.p("Operator transfers token 0 to Alice")

    contract.transfer([
        contract.batch_transfer.item(from_=alice.address,
                               txs=[
                                   sp.record(to_=alice.address, amount=1, token_id=0)
                               ])
    ]).run(sender=op)
    ownership_test(scenario, contract, possessors)

    scenario.p("Operator still has rights on Alice's token 0")
    contract.transfer([
        contract.batch_transfer.item(from_=alice.address,
                               txs=[
                                   sp.record(to_=bob.address, amount=1, token_id=0)
                               ])
    ]).run(sender=op)
    possessors[0] = bob
    ownership_test(scenario, contract, possessors)

    #-----------------------------------------------------
    scenario.h2("Naming operator on balance 0 token")

    possessors = [alice]
    contract = create_new_contract(config, admin, scenario, possessors)

    scenario.p("Bob names operator for token 0 he doesn't possess yet")

    contract.update_operators([
        sp.variant("add_operator", contract.operator_param.make(
            owner=bob.address,
            operator=op.address,
            token_id=0))
    ]).run(sender=bob)

    scenario.p(
        "Alice sends token 0 to Bob. Operator then has right on this token.")

    contract.transfer([
        contract.batch_transfer.item(from_=alice.address,
                               txs=[
                                   sp.record(to_=bob.address,
                                             amount=1,
                                             token_id=0)
                               ])
    ]).run(sender=alice)

    contract.transfer([
        contract.batch_transfer.item(from_=bob.address,
                               txs=[
                                   sp.record(to_=alice.address,
                                             amount=1,
                                             token_id=0)
                               ])
    ]).run(sender=op)
    ownership_test(scenario, contract, possessors)

    #-----------------------------------------------------
    scenario.h2("Naming operator on non-existing token")

    possessors = []
    contract = create_new_contract(config, admin, scenario, possessors)

    contract.update_operators([
        sp.variant("add_operator", contract.operator_param.make(
            owner=admin.address,
            operator=op.address,
            token_id=0))
    ]).run(sender=admin)

    #-----------------------------------------------------
    scenario.h2("Granting in the name of someone else")

    possessors = [alice]
    contract = create_new_contract(config, admin, scenario, possessors)

    scenario.h3("Bob tries to grant Operator rights on Alice's token 0")

    contract.update_operators([
        sp.variant("add_operator", contract.operator_param.make(
            owner=alice.address,
            operator=op.address,
            token_id=0))
    ]).run(sender=bob, valid=False)

    scenario.h3("Admin tries to grant Operator rights on Alice's token 0")

    contract.update_operators([
        sp.variant("add_operator", contract.operator_param.make(
            owner=alice.address,
            operator=op.address,
            token_id=0))
    ]).run(sender=admin, valid=False)

    scenario.h3("Alice itself cannot fake token owner in update_operators")

    contract.update_operators([
        sp.variant("add_operator", contract.operator_param.make(
            owner=admin.address,
            operator=op.address,
            token_id=0))
    ]).run(sender=alice, valid=False)

    #-----------------------------------------------------
    scenario.h2((
        "If one of sub command of update_operators is invalid, whole transaction is canceled\n"
        "Good add, wrong add"
    ))

    possessors = [alice]
    contract = create_new_contract(config, admin, scenario, possessors)

    scenario.h3("Alice makes invalid add request")

    contract.update_operators([
        sp.variant("add_operator", contract.operator_param.make(
            owner=alice.address,
            operator=op.address,
            token_id=0))
    ,
        sp.variant("add_operator", contract.operator_param.make(
            owner=bob.address,
            operator=op.address,
            token_id=0))
    ]).run(sender=alice, valid=False)

    scenario.h3("Operator#1 should not be able to smuggle Alice's token 0")

    contract.transfer([
        contract.batch_transfer.item(from_=alice.address,
                               txs=[
                                   sp.record(to_=bob.address,
                                             amount=1,
                                             token_id=0)
                               ])
    ]).run(sender=op, valid=False)
    ownership_test(scenario, contract, possessors)
