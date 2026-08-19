// Copyright (C) 2020-2022 Intel Corporation
// Copyright (C) CVAT.ai Corporation
//
// SPDX-License-Identifier: MIT

import React, { useState } from 'react';
import { useHistory } from 'react-router';

import { Row, Col } from 'antd/lib/grid';
import { PlusOutlined } from '@ant-design/icons';
import Button from 'antd/lib/button';
import Input from 'antd/lib/input';
import {
    SortingComponent,
    ResourceFilterHOC,
    defaultVisibility,
    ResourceSelectionInfo,
} from 'components/resource-sorting-filtering';
import { TasksQuery } from 'reducers';
import dimensions from 'utils/dimensions';
import {
    localStorageRecentKeyword, localStorageRecentCapacity, predefinedFilterValues, config,
} from './tasks-filter-configuration';

const FilteringComponent = ResourceFilterHOC(
    config, localStorageRecentKeyword, localStorageRecentCapacity, predefinedFilterValues,
);

interface VisibleTopBarProps {
    onApplyFilter(filter: string | null): void;
    onApplySorting(sorting: string | null): void;
    onApplySearch(search: string | null): void;
    query: TasksQuery;
    selectedCount: number;
    onSelectAll: () => void;
}

export default function TopBarComponent(props: Readonly<VisibleTopBarProps>): JSX.Element {
    const {
        query, onApplyFilter, onApplySorting, onApplySearch,
        selectedCount, onSelectAll,
    } = props;
    const [visibility, setVisibility] = useState(defaultVisibility);
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
                    <div>
                        <SortingComponent
                            visible={visibility.sorting}
                            onVisibleChange={(visible: boolean) => (
                                setVisibility({ ...defaultVisibility, sorting: visible })
                            )}
                            defaultFields={query.sort?.split(',') || ['-ID']}
                            sortingFields={['ID', 'Owner', 'Status', 'Assignee', 'Updated date', 'Subset',
                                'Mode', 'Dimension', 'Project ID', 'Name', 'Project name']}
                            onApplySorting={onApplySorting}
                        />
                        <FilteringComponent
                            value={query.filter}
                            predefinedVisible={visibility.predefined}
                            builderVisible={visibility.builder}
                            recentVisible={visibility.recent}
                            onPredefinedVisibleChange={(visible: boolean) => (
                                setVisibility({ ...defaultVisibility, predefined: visible })
                            )}
                            onBuilderVisibleChange={(visible: boolean) => (
                                setVisibility({ ...defaultVisibility, builder: visible })
                            )}
                            onRecentVisibleChange={(visible: boolean) => (
                                setVisibility({ ...defaultVisibility, builder: visibility.builder, recent: visible })
                            )}
                            onApplyFilter={onApplyFilter}
                        />
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
