from mcdreforged.api.command import *

from stats_helper import constants
from stats_helper import quick_scoreboard

stored = quick_scoreboard.quick_scoreboards


class Arguments:
	def __init__(self, content: str, total_length: int):
		self.__arg_set = set(content.split(' '))
		for arg in self.__arg_set:
			if len(arg) > 0 and not arg.startswith('-'):
				raise CommandSyntaxError('Non-arg value "{}" found'.format(content), total_length)

	@classmethod
	def empty(cls):
		return Arguments('', 0)

	@property
	def is_uuid(self) -> bool:
		return '-uuid' in self.__arg_set

	@property
	def is_bot(self) -> bool:
		return '-bot' in self.__arg_set

	@property
	def is_tell(self) -> bool:
		return '-tell' in self.__arg_set

	@property
	def is_all(self) -> bool:
		return '-all' in self.__arg_set


class ArgumentEnding(ArgumentNode):
	def parse(self, text: str) -> ParseResult:
		return ParseResult(Arguments(text, len(text)), len(text))


class NameAndArgumentEnding(QuotableText):
	def parse(self, text: str) -> ParseResult:
		parse_name = super(NameAndArgumentEnding, self).parse(text)
		name = parse_name.value
		value_name = None
		if not name.startswith('-'):
			value_name = name
			text_for_arguments = text[parse_name.char_read:]
		else:
			text_for_arguments = text
		return ParseResult((value_name, Arguments(text_for_arguments, len(text))), len(text))


class UnknownQuickScoreboard(IllegalArgument):
	def __init__(self, message: str, char_read: int, alias: str):
		super().__init__(message, char_read)
		self.alias = alias

	def get_error_data(self) -> tuple:
		return (self.alias, )


class ScoreboardQuery(ArgumentNode):
	def __init__(self, name: str, *, allow_all_tag: bool = False):
		super().__init__(name)
		self.allow_all_tag = allow_all_tag

	def parse(self, text: str) -> ParseResult:
		arg1 = command_builder_util.get_element(text)
		scoreboard = stored.get(arg1)
		if scoreboard is not None:
			return ParseResult(scoreboard, len(arg1))  # <alias>
		remaining = command_builder_util.remove_divider_prefix(text[len(arg1):])
		arg2 = command_builder_util.get_element(remaining)
		if (self.allow_all_tag and arg2 == constants.AllTargetTag) or (len(arg2) > 0 and arg2[0].isalpha()):
			return ParseResult((arg1, arg2), len(text) - len(remaining) + len(arg2))  # <cls> <target>
		else:
			raise UnknownQuickScoreboard('Unknown scoreboard {}'.format(arg1), len(arg1), arg1)
