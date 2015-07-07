import shutil

from coalib.results.Result import Result
from coalib.output.printers.Printer import Printer
from coalib.misc.i18n import _

class Interactor(Printer):
    def __init__(self, log_printer):
        Printer.__init__(self)
        self.log_printer = log_printer
        self.file_diff_dict = {}
        self.current_section = None

    def _print_result(self, result):
        """
        Prints the result.
        """
        raise NotImplementedError

    def _print_actions(self, actions):
        """
        Prints the given actions and lets the user choose.

        :param actions: A list of FunctionMetadata objects.
        :return:        A touple with the name member of the FunctionMetadata
                        object chosen by the user and a Section containing at
                        least all needed values for the action. If the user did
                        choose to do nothing, return (None, None).
        """
        raise NotImplementedError

    def _print_action_failed(self, action_name, exception):
        """
        Prints out the information that the chosen action failed.

        :param action_name: The name of the action that failed.
        :param exception:   The exception with which it failed.
        """
        raise NotImplementedError

    def print_result(self, result, file_dict):
        """
        Prints the result appropriate to the output medium.

        :param result:    A derivative of Result.
        :param file_dict: A dictionary containing all files with filename as
                          key.
        """
        if not isinstance(result, Result):
            self.log_printer.warn(_("One of the results can not be printed "
                                    "since it is not a valid derivative of "
                                    "the coala result class."))
            return

        self._print_result(result)

        actions = result.get_actions()
        if actions == []:
            return

        action_dict = {}
        metadata_list = []
        for action in actions:
            metadata = action.get_metadata()
            action_dict[metadata.name] = action
            metadata_list.append(metadata)

        # User can always choose no action which is guaranteed to succeed
        while not self.apply_action(metadata_list,
                                    action_dict,
                                    result,
                                    file_dict):
            pass

    def apply_action(self,
                     metadata_list,
                     action_dict,
                     result,
                     file_dict):
        action_name, section = self._print_actions(metadata_list)
        if action_name is None:
            return True

        chosen_action = action_dict[action_name]
        try:
            chosen_action.apply_from_section(result,
                                             file_dict,
                                             self.file_diff_dict,
                                             section)
        except Exception as exception:  # pylint: disable=broad-except
            self._print_action_failed(action_name, exception)
            return False

        return True

    def acquire_settings(self, settings):
        """
        This method prompts the user for the given settings.

        :param settings: a dictionary with the settings name as key and a list
                         containing a description in [0] and the name of the
                         bears who need this setting in [1] and following.
                         Example:
        {"UseTabs": ["describes whether tabs should be used instead of spaces",
                     "SpaceConsistencyBear",
                     "SomeOtherBear"]}

        :return:         a dictionary with the settings name as key and the
                         given value as value.
        """
        raise NotImplementedError

    def finalize(self, file_dict):
        """
        To be called after all results are given to the interactor.
        """
        for filename in self.file_diff_dict:
            diff = self.file_diff_dict[filename]
            file_dict[filename] = diff.apply(file_dict[filename])

            # Backup original file, override old backup if needed
            shutil.copy2(filename, filename + ".orig")

            # Write new contents
            with open(filename, mode='w') as file:
                file.writelines(file_dict[filename])

    def begin_section(self, section):
        """
        Will be called before the results for a section come in (via
        print_results).

        :param section: The section that will get executed now.
        """
        self.file_diff_dict = {}
        self.current_section = section
        self._print_section_beginning(section)

    def _print_section_beginning(self, section):
        """
        Will be called after initialization current_section in
        begin_section()

        :param section: The section that will get executed now.
        """
        raise NotImplementedError

    def show_bears(self, bears):
        """
        It presents the bears to the user and information about each bear.

        :param bears: A dictionary containing bears as keys and a list of
                      sections which the bear belongs as the value.
        """
        raise NotImplementedError

    def did_nothing(self):
        """
        Will be called after processing a coafile when nothing had to be done,
        i.e. no section was enabled/targeted.
        """
        raise NotImplementedError
