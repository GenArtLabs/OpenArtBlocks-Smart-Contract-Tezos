def run_tests_is_operator(config):
    scenario = sp.test_scenario()

    admin, [alice, bob] = get_addresses()
    op = sp.test_account("Operator")

    scenario.h1("Is operator tests")

    scenario.table_of_contents()

    #-----------------------------------------------------
    scenario.h2("Non-existing token, no operator")
    contract = create_new_contract(config, admin, scenario, [])

    is_op = contract.is_operator(
        sp.record(owner=alice.address, operator=op.address, token_id=0)
    )
    scenario.verify(is_op == False)

    #-----------------------------------------------------
    scenario.h2("Existing token, owner")
    contract = create_new_contract(config, admin, scenario, [alice])

    is_op = contract.is_operator(
        sp.record(owner=alice.address, operator=alice.address, token_id=0)
    )
    scenario.verify(is_op == True)

    #-----------------------------------------------------
    scenario.h2("Existing token, no owner, no operator")
    contract = create_new_contract(config, admin, scenario, [alice])

    is_op = contract.is_operator(
        sp.record(owner=alice.address, operator=op.address, token_id=0)
    )
    scenario.verify(is_op == False)

    #-----------------------------------------------------
    scenario.h2("Non-existing token, owner")
    contract = create_new_contract(config, admin, scenario, [])

    is_op = contract.is_operator(
        sp.record(owner=alice.address, operator=alice.address, token_id=0)
    )
    scenario.verify(is_op == True)

    #-----------------------------------------------------
    scenario.h2("Non-existing token, operator")
    contract = create_new_contract(config, admin, scenario, [])

    contract.update_operators([
        sp.variant("add_operator", contract.operator_param.make(
            owner=alice.address,
            operator=op.address,
            token_id=0))
    ]).run(sender=alice)

    is_op = contract.is_operator(
        sp.record(owner=alice.address, operator=op.address, token_id=0)
    )
    scenario.verify(is_op == True)

    #-----------------------------------------------------
    scenario.h2("Existing token, operator")
    contract = create_new_contract(config, admin, scenario, [alice])

    contract.update_operators([
        sp.variant("add_operator", contract.operator_param.make(
            owner=alice.address,
            operator=op.address,
            token_id=0))
    ]).run(sender=alice)

    is_op = contract.is_operator(
        sp.record(owner=alice.address, operator=op.address, token_id=0)
    )
    scenario.verify(is_op == True)
