import irsdk
from iracing.IrTypes import SyncState
from iracing.IrTypes import LapData

class IrTypesTest:

    def testLapData(self):
        ir = irsdk.IRSDK()
        ir.startup(test_file='data/monzasunset.dump')

        syncState = SyncState()
        syncState.updateSession('session', 'subsession', '0')
        lapData = LapData(syncState, ir)

        print(syncState.toDict())
        print(lapData.lapDataMessage())

        ir.shutdown()

    def testPitstopMessage(self):

        syncState = SyncState()
        syncState.updateSession('session', 'subsession', '0')
        syncState.lap = 2

        #irsdk_NotInWorld       -1
        #irsdk_OffTrack          0
        #irsdk_InPitStall        1
        #irsdk_AproachingPits    2
        #irsdk_OnTrack           3
        syncState.updatePits(2, 3, 0.1 * 86400)
        print(syncState.pitstopDataMessage())

        syncState.updatePits(2, 2, 0.2 * 86400)
        print(syncState.pitstopDataMessage())

        syncState.updatePits(2, 2, 0.3 * 86400)
        print(syncState.pitstopDataMessage())

        syncState.updatePits(2, 1, 0.4 * 86400)
        print(syncState.pitstopDataMessage())

        syncState.updatePits(2, 2, 0.5 * 86400)
        print(syncState.pitstopDataMessage())

        syncState.updatePits(2, 2, 0.6 * 86400)
        print(syncState.pitstopDataMessage())

        syncState.updatePits(2, 3, 0.7 * 86400)
        print(syncState.pitstopDataMessage())

        syncState.updatePits(3, 3, 0.7 * 86400)
        print(syncState.pitstopDataMessage())

        syncState.updatePits(3, 2, 0.8 * 86400)
        print(syncState.pitstopDataMessage())

if __name__ == "__main__":
    test = IrTypesTest()

    #test.testLapData()
    test.testPitstopMessage()