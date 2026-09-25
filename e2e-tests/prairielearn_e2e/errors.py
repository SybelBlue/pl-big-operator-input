"""Errors raised by the PrairieLearn end-to-end harness."""


class HarnessError(AssertionError):
    """A selected question violated the PrairieLearn lifecycle contract."""


class UnsupportedQuestion(HarnessError):
    """A selected question uses a format that this harness does not execute."""
