'''
A class containing useful functions that do not exist either in base python or easily googleable python packages.
'''
class JeffUtility(object):

    @staticmethod
    def dict_generator(indict, pre=None):
        '''
        Summary:
            Returns linear lists of an arbitrarily nested dictionary.  All credit for this function goes to Bryukhanov Valentin (http://stackoverflow.com/questions/12507206/python-recommended-way-to-walk-complex-dictionary-structures-imported-from-json).
        Args:
            indict: The dictionary to convert to linear lists.
            pre: Not sure what this does.
        Returns:
            A linear list representation of a nested dictionary.
        '''

        pre = pre[:] if pre else []
        if isinstance(indict, dict):
            for key, value in indict.items():
                if isinstance(value, dict):
                    for d in JeffUtility.dict_generator(value, [key] + pre):
                        yield d
                elif isinstance(value, list) or isinstance(value, tuple):
                    for v in value:
                        for d in JeffUtility.dict_generator(v, [key] + pre):
                            yield d
                else:
                    yield pre + [key, value]
        else:
            yield indict


    @staticmethod
    def convert_decimal_to_base(n, base):
        '''
        Summary:
            Convert positive decimal integer n to equivalent in another base (2-36).
        Args:
            n: A base 10 integer to be converted to some arbitrary base (2-36).
            base: An integer specifying the base to convert the integer to.
        Returns:
            s: A string representing the integer of the new base.
        '''

        digits = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"

        try:
            n = int(n)
            base = int(base)
        except:
            return ""

        if n < 0 or base < 2 or base > 36:
            return ""

        s = ""
        while 1:
            r = n % base
            s = digits[r] + s
            n = n / base
            if n == 0:
                break

        return s


    @staticmethod
    def convert_base_to_decimal(s, base):
        '''
        Summary:
            Convert an integer of an arbitrary base (base 2-36) into a decimal integer.
        Args:
            s: A string specifying an integer of some arbitrary base (2-36).
            base: An integer specifying the base of the number.
        Returns:
            n: An integer; the base 10 version of s.
        '''

        digits = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"

        n = 0
        exp = 0

        try:
            for char in s[::-1]:
                value = digits.index(char.upper())
                n = n + value * (base ** exp)
                exp = exp + 1
        except:
            return -1  # error

        return n