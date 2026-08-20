// Copyright (C) 2020-2022 Intel Corporation
// Copyright (C) CVAT.ai Corporation
//
// SPDX-License-Identifier: MIT

import React from 'react';
import { useHistory } from 'react-router';

import { Row, Col } from 'antd/lib/grid';
import { PlusOutlined } from '@ant-design/icons';
import Button from 'antd/lib/button';
import Input from 'antd/lib/input';
import { ResourceSelectionInfo } from 'components/resource-sorting-filtering';
import { TasksQuery } from 'reducers';
import dimensions from 'utils/dimensions';

interface VisibleTopBarProps {
    onApplySearch(search: string | null): void;
    query: TasksQuery;
    selectedCount: number;
    onSelectAll: () => void;
}

export default function TopBarComponent(props: Readonly<VisibleTopBarProps>): JSX.Element {
    const {
        query, onApplySearch,
        selectedCount, onSelectAll,
    } = props;
    const history = useHistory();

    return (
        <Row className='cvat-tasks-page-top-bar cvat-resource-top-bar-wrapper' justify='center' align='middle'>
            <Col {...dimensions}>
                <div className='cvat-tasks-page-filters-wrapper'>
                    <div>
                        <Input.Search
                            enterButton
                            onSearch={(phrase: string) => {
                                onApplySearch(phrase);
                            }}
                            defaultValue={query.search ?? ''}
                            className='cvat-tasks-page-search-bar'
                            placeholder='搜索任务'
                        />
                        <ResourceSelectionInfo selectedCount={selectedCount} onSelectAll={onSelectAll} />
                    </div>
                </div>
                <div>
                    <Button
                        type='primary'
                        className='cvat-create-task-dropdown'
                        icon={<PlusOutlined />}
                        title='新建任务'
                        aria-label='新建任务'
                        onClick={(): void => history.push('/tasks/create')}
                    >
                        新建任务
                    </Button>
                </div>
            </Col>
        </Row>
    );
}
