const commandMap = [
  {
    command: 'lidar',
    mnemonic: 'LDA[0]',
    usage1: '[lidar name or ID]',
    usage2: '[lidar operations]{open, close, start_record, stop_record}',
    usage3: '[other parameters]'
  },
  {
    command: 'camera',
    mnemonic: 'CMA[1]',
    usage1: '[camera name or ID]',
    usage2: '[camera operations]{open, close, start_record, stop_record}',
    usage3: '[other parameters]'
  }
]

export default commandMap
