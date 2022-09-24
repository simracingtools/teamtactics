import irsdk
import iracing
from iracing.IrTypes import SyncState
from iracing.IrTypes import LapData

class IrTypesTest:

    def testLapData(self):
        ir = irsdk.IRSDK()
        ir.startup(test_file='data/monzasunset.dump')

        syncState = SyncState()
        syncState.sessionId = 'session'
        syncState.subSessionId = 'subsession'
        syncState.sessionNum = 0

        lapData = LapData(syncState, ir)

        print(syncState.toDict())
        print(lapData.lapDataMessage())

        ir.shutdown()

    def testSessionFlags(self):
        print(str(hex(268697600)))
        flags = iracing.check_session_flags(268697600)
        print(flags)


if __name__ == "__main__":
    test = IrTypesTest()

    #test.testLapData()
    test.testSessionFlags()