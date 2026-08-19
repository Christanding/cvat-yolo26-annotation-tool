// Copyright (C) 2020-2022 Intel Corporation
// Copyright (C) CVAT.ai Corporation
//
// SPDX-License-Identifier: MIT

import React, { useEffect, useState } from 'react';
import Text from 'antd/lib/typography/Text';
import { StatesOrdering, Workspace } from 'reducers';
import {
    FRAME_STATUS_UPDATED_EVENT,
    FrameReviewStatus,
    getFrameStatus,
} from 'utils/local-api';

interface Props {
    workspace: Workspace;
    statesHidden: boolean;
    statesLocked: boolean;
    statesCollapsed: boolean;
    statesOrdering: StatesOrdering;
    switchLockAllShortcut: string;
    switchHiddenAllShortcut: string;
    showGroundTruth: boolean;
    count: number;
    taskID: number;
    frameNumber: number;
    changeStatesOrdering(value: StatesOrdering): void;
    lockAllStates(): void;
    unlockAllStates(): void;
    collapseAllStates(): void;
    expandAllStates(): void;
    hideAllStates(): void;
    showAllStates(): void;
    changeShowGroundTruth(): void;
}

export default function ObjectListHeader(props: Props): JSX.Element {
    const {
        count, frameNumber, taskID,
    } = props;
    const [savedStatus, setSavedStatus] = useState<FrameReviewStatus | null>(null);

    useEffect(() => {
        let active = true;
        setSavedStatus(null);
        getFrameStatus(taskID, frameNumber)
            .then(({ status }) => {
                if (active) setSavedStatus(status);
            })
            .catch(() => {
                if (active) setSavedStatus('unreviewed');
            });
        return () => {
            active = false;
        };
    }, [taskID, frameNumber]);

    useEffect(() => {
        const onStatusUpdated = (event: Event): void => {
            const detail = (event as CustomEvent<{
                taskID: number;
                frame: number;
                status: FrameReviewStatus;
            }>).detail;
            if (detail.taskID === taskID && detail.frame === frameNumber) {
                setSavedStatus(detail.status);
            }
        };
        window.addEventListener(FRAME_STATUS_UPDATED_EVENT, onStatusUpdated);
        return () => window.removeEventListener(FRAME_STATUS_UPDATED_EVENT, onStatusUpdated);
    }, [taskID, frameNumber]);

    const status = count > 0 ? 'annotated' : savedStatus;
    const statusText = {
        annotated: '已标注',
        empty: '已确认无目标',
        unreviewed: '未检查',
    }[status || 'unreviewed'];

    return (
        <div className='cvat-objects-sidebar-states-header'>
            <Text>{`标注框数量：${count}`}</Text>
            <Text type='secondary'>{`图片状态：${statusText}`}</Text>
        </div>
    );
}
