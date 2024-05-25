import math


class Calculos:

    def calcular_st_ht(self, xpatual):

        xp = int(xpatual)
        st_ht = math.floor(xp / 10)
        return st_ht

    def calcular_dx_iq(self, xpatual):

        xp = int(xpatual)
        dx_iq = math.floor(xp / 20)
        return dx_iq


# calcular = Calculos()
# print(calcular.calcular_st_ht("20"))
