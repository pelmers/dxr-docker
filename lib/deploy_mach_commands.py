# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from mach.decorators import (
    CommandArgument,
    CommandProvider,
    Command,
)


@CommandProvider
class DeployCommands(object):
    def __init__(self, context):
        lm = context.log_manager
        lm.enable_unstructured()

    @Command('dxrmo', category='deploy',
             description='Deploy dxr.mozilla.org')
    @CommandArgument('--verbosity', type=int,
                     help='How verbose to be with output')
    def dxrmo(self, verbosity=None):
        # from vcttesting.deploy import deploy_hgmo as deploy
        from deploy import deploy_dxrmo as deploy
        return deploy(verbosity=verbosity)

    @Command('update-config', category='deploy',
             description='Regenerate DXR and Jenkins configs')
    @CommandArgument('--verbosity', type=int,
                     help='How verbose to be with output')
    def update_config(self, verbosity=None):
        from deploy import deploy_update_config as update_config
        return update_config(verbosity=verbosity)

    @Command('restart-builder', category='deploy',
             description='Restart docker on a builder node')
    @CommandArgument('node',
                     help='Node on which to restart docker')
    @CommandArgument('--verbosity', type=int,
                     help='How verbose to be with output')
    def restart_builder(self, node, verbosity=None):
        from deploy import deploy_restart_builder as restart_builder
        return restart_builder(node, verbosity=verbosity)

#    @Command('trigger-build', category='deploy',
#             description='Schedule jenkins index run')
#    @CommandArgument('jobs', nargs='*',
#                     help='Jobs to schedule')
#    @CommandArgument('--verbosity', type=int,
#                     help='How verbose to be with output')
#    def trigger_build(self, jobs, verbosity=None):
#        from deploy import deploy_trigger_build as trigger_build
#        return trigger_build(jobs, verbosity=verbosity)

    @Command('trigger-all', category='deploy',
             description='Schedule all Jenkins jobs to run')
    @CommandArgument('--verbosity', type=int,
                     help='How verbose to be with output')
    def trigger_all(self, verbosity=None):
        from deploy import deploy_trigger_all as trigger_all
        return trigger_all(verbosity=verbosity)
