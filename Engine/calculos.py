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

    def calcular_xp_st_ht(self, xpgasto, xpatual):
        xp_gasto_st_ht = xpatual
        xp_gasto_st_ht += int(xpgasto)
        return xp_gasto_st_ht

    def calcular_xp_dx_iq(self, xpgasto, xpatual):
        xp_gasto_dx_iq = xpatual
        xp_gasto_dx_iq += int(xpgasto)
        return xp_gasto_dx_iq
