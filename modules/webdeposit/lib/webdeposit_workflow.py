

class WebDepositWorkflow(object):
    """ class for running sequential workflows
    The workflow functions must have the following structure

    def function_name(arg1, arg2):
        def fun_name2(obj, eng):
            # do stuff
        return fun_name2
    """

    def __init__(self, obj=None, eng=None, workflow=None):
        if obj is None:
            obj = dict()
        self.eng = eng
        self.current_step = 0
        self.workflow_dict = dict()
        if workflow is not None:
            self.steps_num = len(workflow)
            step_id = 0
            for f in workflow:
                self.workflow_dict[step_id] = f
                step_id += 1

    def set_workflow(self, workflow):
        self.current_step = 0
        self.workflow_dict = dict()
        self.steps_num = len(workflow)
        step_id = 0
        for f in workflow:
            self.workflow_dict[step_id] = f
            step_id += 1

    def run_workflow(self):
        while self.run_next_step():
            pass

    def run_next_step(self):
        if self.current_step >= self.steps_num:
            return False
        function = self.workflow_dict[self.current_step]
        function(self.obj, self.eng)
        self.current_step += 1
        self.obj['step'] = current_step
        return True

    def jump_forward(self):
        self.current_step += 1
        result = self.run_next_step()
        return result

    def jump_backwards(self):
        if self.current_step >= 2:
            self.current_step -= 1
        else:
            self.current_step = 1
        result = self.run_next_step()
        return result

    def set_current_step(self, step):
        self.current_step = step

    def get_current_step(self):
        return self.current_step
