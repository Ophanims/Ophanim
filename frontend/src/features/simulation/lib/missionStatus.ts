import {
CheckIcon,
ClockIcon,
CloudArrowDownIcon,
CloudArrowUpIcon,
GlobeAltIcon,
XMarkIcon
} from "@heroicons/react/24/solid";

const MissionStatusCode = {
    "Confirmed": 0,
    "Tasking": 1,
    "Acquiring": 2,
    "Delivering": 3,
    "Completed": 4,
    "Incomplete": 5,
};
const MissionStatus = [
    { name: "Confirmed", icon: ClockIcon },
    { name: "Tasking", icon: CloudArrowUpIcon },
    { name: "Acquiring", icon: GlobeAltIcon },
    { name: "Delivering", icon: CloudArrowDownIcon },
    { name: "Completed", icon: CheckIcon },
    { name: "Incomplete", icon: XMarkIcon },
];

export { MissionStatus,MissionStatusCode };
