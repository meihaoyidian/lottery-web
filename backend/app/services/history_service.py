"""
历史记录服务
处理已完成推荐的查询、统计和准确率计算
"""
import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session

from app.models.recommendation import Recommendation, RecommendationStatus

logger = logging.getLogger(__name__)


class HistoryService:
    """历史记录业务逻辑"""

    @staticmethod
    def _is_accurate_status(hit_status: str) -> bool:
        """判断命中状态是否算作命中（hit 或 push/走水 都算命中）"""
        if not hit_status:
            return False
        return hit_status.strip().lower() in ('hit', 'push')

    @staticmethod
    def get_history_recommendations(
        db: Session,
        prediction_type: Optional[str] = None,
        month: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        page: int = 1,
        page_size: int = 20,
        is_paid_user: bool = True
    ) -> Dict[str, Any]:
        """
        获取历史推荐列表（仅已完成的推荐）

        Args:
            db: 数据库会话
            prediction_type: 预测类型过滤
            month: 月份过滤，格式：YYYY-MM
            start_date: 开始日期
            end_date: 结束日期
            page: 页码
            page_size: 每页数量
            is_paid_user: 是否为付费用户（非付费用户只看高命中率推荐）

        Returns:
            包含推荐列表和分页信息的字典
        """
        # 构建查询（默认显示全部历史数据）
        query = db.query(Recommendation).filter(
            Recommendation.status == RecommendationStatus.COMPLETED,
            Recommendation.archived_at.isnot(None)
        )

        # 添加过滤条件
        if prediction_type:
            query = query.filter(Recommendation.prediction_type == prediction_type)

        # 月份过滤
        if month:
            try:
                year, month_num = month.split('-')
                year = int(year)
                month_num = int(month_num)

                # 计算月份的开始和结束日期
                month_start = datetime(year, month_num, 1)
                if month_num == 12:
                    month_end = datetime(year + 1, 1, 1)
                else:
                    month_end = datetime(year, month_num + 1, 1)

                query = query.filter(
                    Recommendation.created_at >= month_start,
                    Recommendation.created_at < month_end
                )
            except (ValueError, AttributeError):
                pass  # 如果月份格式不正确，忽略此过滤条件

        if start_date:
            query = query.filter(Recommendation.created_at >= start_date)

        if end_date:
            query = query.filter(Recommendation.created_at <= end_date)

        # 按归档时间降序排列
        query = query.order_by(Recommendation.archived_at.desc())

        # 非付费用户：只展示命中率高的推荐（actual_outcome.hit_status='hit'）
        if not is_paid_user:
            rec_ids = HistoryService.get_highlight_ids(db, limit=10)
            if rec_ids:
                items = query.filter(Recommendation.id.in_(rec_ids)).order_by(Recommendation.archived_at.desc()).all()
            else:
                items = []

            return {
                'items': items,
                'total': len(items),
                'page': 1,
                'page_size': page_size,
                'has_more': False,
                'is_preview': True
            }

        # 付费用户：返回全部数据
        # 获取总数
        total = query.count()

        # 分页
        offset = (page - 1) * page_size
        items = query.offset(offset).limit(page_size).all()

        return {
            'items': items,
            'total': total,
            'page': page,
            'page_size': page_size,
            'has_more': offset + len(items) < total,
            'is_preview': False
        }

    @staticmethod
    def _filter_high_accuracy_recommendations(recommendations: List[Recommendation]) -> List[Recommendation]:
        """
        筛选高命中率推荐（允许最多1场错误）

        筛选规则：
        1. 推荐级别 hit_status 为 'hit' 的直接保留
        2. 推荐级别 hit_status 为 'partial' 或其他，检查单场命中情况
        3. 单场错误数 <= 1 的推荐保留
        4. 没有 prediction_data 的推荐默认保留（兼容旧数据）

        Args:
            recommendations: 推荐列表

        Returns:
            筛选后的推荐列表
        """
        filtered = []
        miss_count = 0  # 记录被过滤掉的推荐数量

        for rec in recommendations:
            # 检查推荐级别命中状态
            if rec.actual_outcome:
                hit_status = rec.actual_outcome.get('hit_status', '')

                # 命中的推荐直接保留
                if HistoryService._is_accurate_status(hit_status):
                    filtered.append(rec)
                    continue

            # 检查单场命中情况
            if not rec.prediction_data:
                # 没有 prediction_data 的推荐默认保留（兼容旧数据）
                filtered.append(rec)
                continue

            single_matches = rec.prediction_data.get('single_matches', [])
            if not single_matches:
                # 没有单场数据的推荐默认保留
                filtered.append(rec)
                continue

            # 统计错误场次
            miss_matches = 0
            for match in single_matches:
                raw_status = match.get('hit_status')
                if raw_status and raw_status != 'None' and raw_status not in (None, ''):
                    status = str(raw_status).strip().lower()
                    # push/走水 不算失误，只统计明确的 miss
                    if status == 'miss':
                        miss_matches += 1

            # 错误数 <= 1 的保留，否则过滤（更严格的筛选）
            if miss_matches <= 1:
                filtered.append(rec)
            else:
                miss_count += 1

        logger.info(f"非付费用户筛选：总推荐 {len(recommendations)}，保留 {len(filtered)}，过滤 {miss_count}")
        return filtered

    @staticmethod
    def get_statistics(
        db: Session,
        prediction_type: Optional[str] = None,
        month: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        is_paid_user: bool = True
    ) -> Dict[str, Any]:
        """
        计算历史推荐的统计数据（按单场维度统计）

        Args:
            db: 数据库会话
            prediction_type: 预测类型过滤
            month: 月份过滤，格式：YYYY-MM
            start_date: 开始日期
            end_date: 结束日期
            is_paid_user: 是否为付费用户
                - 付费用户：统计所有场次的真实命中率
                - 非付费用户：先筛选高命中率推荐，统计时排除miss场次

        Returns:
            统计数据字典
        """
        # 构建查询（默认统计全部历史数据）
        query = db.query(Recommendation).filter(
            Recommendation.status == RecommendationStatus.COMPLETED,
            Recommendation.archived_at.isnot(None)
        )

        # 添加过滤条件
        if prediction_type:
            query = query.filter(Recommendation.prediction_type == prediction_type)

        # 月份过滤
        if month:
            try:
                year, month_num = month.split('-')
                year = int(year)
                month_num = int(month_num)

                # 计算月份的开始和结束日期
                month_start = datetime(year, month_num, 1)
                if month_num == 12:
                    month_end = datetime(year + 1, 1, 1)
                else:
                    month_end = datetime(year, month_num + 1, 1)

                query = query.filter(
                    Recommendation.created_at >= month_start,
                    Recommendation.created_at < month_end
                )
            except (ValueError, AttributeError):
                pass  # 如果月份格式不正确，忽略此过滤条件

        if start_date:
            query = query.filter(Recommendation.created_at >= start_date)

        if end_date:
            query = query.filter(Recommendation.created_at <= end_date)

        all_recommendations = query.all()
        total_recs_count = len(all_recommendations)

        recommendations = all_recommendations

        # 初始化统计数据
        total_single_matches = 0
        accurate_single_matches = 0

        football_single_matches = 0
        football_accurate_singles = 0
        football_parlay_total = 0
        football_parlay_accurate = 0

        basketball_single_matches = 0
        basketball_accurate_singles = 0
        basketball_parlay_total = 0
        basketball_parlay_accurate = 0

        # 重心场次统计
        key_match_total = 0
        key_match_accurate = 0

        # 重心场次分类型统计
        football_key_match_total = 0
        football_key_match_accurate = 0
        basketball_key_match_total = 0
        basketball_key_match_accurate = 0

        # 遍历所有推荐，按单场统计
        for rec in recommendations:
            if not rec.prediction_data:
                continue

            prediction_data = rec.prediction_data
            is_football = rec.prediction_type == "football"

            single_matches = prediction_data.get('single_matches', [])

            # 统计单场
            for match in single_matches:
                # 处理 hit_status，支持多种格式
                raw_status = match.get('hit_status')
                # 处理字符串 'None' 的情况
                if raw_status == 'None' or raw_status is None or raw_status == '':
                    hit_status = ''
                else:
                    hit_status = str(raw_status).strip().lower()

                # 总单场统计（包括空 hit_status）
                total_single_matches += 1
                if HistoryService._is_accurate_status(hit_status):
                    accurate_single_matches += 1

                # 分类型统计
                if is_football:
                    football_single_matches += 1
                    if HistoryService._is_accurate_status(hit_status):
                        football_accurate_singles += 1
                else:
                    basketball_single_matches += 1
                    if HistoryService._is_accurate_status(hit_status):
                        basketball_accurate_singles += 1

                # 重心场次统计（按单场维度）
                if match.get('is_key_match', False):
                    key_match_total += 1
                    if HistoryService._is_accurate_status(hit_status):
                        key_match_accurate += 1
                    if is_football:
                        football_key_match_total += 1
                        if HistoryService._is_accurate_status(hit_status):
                            football_key_match_accurate += 1
                    else:
                        basketball_key_match_total += 1
                        if HistoryService._is_accurate_status(hit_status):
                            basketball_key_match_accurate += 1

            # 统计组合（支持多个组合）
            parlays = prediction_data.get('parlays', [])
            # 兼容旧数据格式（单个 parlay）
            if not parlays and 'parlay' in prediction_data:
                old_parlay = prediction_data.get('parlay')
                if old_parlay:
                    parlays = [old_parlay]

            for parlay in parlays:
                if parlay and parlay.get('hit_status'):
                    # 处理组合的 hit_status
                    raw_parlay_status = parlay.get('hit_status')
                    if raw_parlay_status == 'None' or raw_parlay_status is None or raw_parlay_status == '':
                        parlay_hit_status = ''
                    else:
                        parlay_hit_status = str(raw_parlay_status).strip().lower()

                    if is_football:
                        football_parlay_total += 1
                        if HistoryService._is_accurate_status(parlay_hit_status):
                            football_parlay_accurate += 1
                    else:
                        basketball_parlay_total += 1
                        if HistoryService._is_accurate_status(parlay_hit_status):
                            basketball_parlay_accurate += 1

        # 计算准确率
        overall_rate = round(accurate_single_matches / total_single_matches * 100, 2) if total_single_matches > 0 else 0.0

        football_rate = round(football_accurate_singles / football_single_matches * 100, 2) if football_single_matches > 0 else 0.0
        football_parlay_rate = round(football_parlay_accurate / football_parlay_total * 100, 2) if football_parlay_total > 0 else 0.0

        basketball_rate = round(basketball_accurate_singles / basketball_single_matches * 100, 2) if basketball_single_matches > 0 else 0.0
        basketball_parlay_rate = round(basketball_parlay_accurate / basketball_parlay_total * 100, 2) if basketball_parlay_total > 0 else 0.0

        # 重心场次准确率
        key_match_rate = round(key_match_accurate / key_match_total * 100, 2) if key_match_total > 0 else 0.0
        football_key_match_rate = round(football_key_match_accurate / football_key_match_total * 100, 2) if football_key_match_total > 0 else 0.0
        basketball_key_match_rate = round(basketball_key_match_accurate / basketball_key_match_total * 100, 2) if basketball_key_match_total > 0 else 0.0

        result = {
            'total_count': total_single_matches,
            'accurate_count': accurate_single_matches,
            'accuracy_rate': overall_rate,
            'total_recs_count': total_recs_count,
        }

        # 所有用户：返回分类明细和重心场次统计
        result.update({
            'football_stats': {
                'total': football_single_matches,
                'accurate': football_accurate_singles,
                'rate': football_rate,
                'parlay_total': football_parlay_total,
                'parlay_accurate': football_parlay_accurate,
                'parlay_rate': football_parlay_rate,
                'key_match_total': football_key_match_total,
                'key_match_accurate': football_key_match_accurate,
                'key_match_rate': football_key_match_rate
            },
            'basketball_stats': {
                'total': basketball_single_matches,
                'accurate': basketball_accurate_singles,
                'rate': basketball_rate,
                'parlay_total': basketball_parlay_total,
                'parlay_accurate': basketball_parlay_accurate,
                'parlay_rate': basketball_parlay_rate,
                'key_match_total': basketball_key_match_total,
                'key_match_accurate': basketball_key_match_accurate,
                'key_match_rate': basketball_key_match_rate
            },
            'key_match_stats': {
                'total': key_match_total,
                'accurate': key_match_accurate,
                'rate': key_match_rate,
                'football_total': football_key_match_total,
                'football_accurate': football_key_match_accurate,
                'football_rate': football_key_match_rate,
                'basketball_total': basketball_key_match_total,
                'basketball_accurate': basketball_key_match_accurate,
                'basketball_rate': basketball_key_match_rate
            }
        })

        return result

    @staticmethod
    def _is_prediction_accurate(recommendation: Recommendation) -> bool:
        """
        判断预测是否准确
        根据命中状态判断：hit 为准确，partial 和 miss 为不准确

        Args:
            recommendation: 推荐对象

        Returns:
            是否准确
        """
        if not recommendation.actual_outcome:
            return False

        # 检查命中状态（hit 或 push/走水 都算命中）
        hit_status = recommendation.actual_outcome.get('hit_status', '')
        return HistoryService._is_accurate_status(hit_status)

    @staticmethod
    def complete_recommendation(
        db: Session,
        recommendation_id: int,
        actual_outcome: Dict[str, Any]
    ) -> Recommendation:
        """
        完成推荐并记录实际结果

        自动将推荐级别的 hit_status 应用到每个单场比赛和组合

        Args:
            db: 数据库会话
            recommendation_id: 推荐ID
            actual_outcome: 实际比赛结果，格式: {'hit_status': 'hit/miss/partial', 'notes': '...'}

        Returns:
            更新后的推荐对象

        Raises:
            ValueError: 如果推荐不存在或已删除
        """
        recommendation = db.query(Recommendation).filter(
            Recommendation.id == recommendation_id
        ).first()

        if not recommendation:
            raise ValueError('推荐不存在')

        if recommendation.status == RecommendationStatus.INACTIVE:
            raise ValueError('该推荐已删除，无法完成')

        # 获取推荐级别的命中状态
        hit_status = actual_outcome.get('hit_status', 'miss')

        # 更新 prediction_data，为每个单场比赛和组合添加 hit_status
        if recommendation.prediction_data:
            prediction_data = recommendation.prediction_data.copy()

            # 更新每个单场比赛的 hit_status
            if 'single_matches' in prediction_data and prediction_data['single_matches']:
                for match in prediction_data['single_matches']:
                    # 如果单场已经有 hit_status，保留（支持更细粒度的标记）
                    # 但要排除 None、'None'、空字符串等无效值
                    existing_status = match.get('hit_status')
                    if not existing_status or existing_status == 'None' or existing_status in ['', None]:
                        match['hit_status'] = hit_status

            # 更新组合的 hit_status（支持多个组合）
            parlays = prediction_data.get('parlays', [])
            # 兼容旧数据格式（单个 parlay）
            if not parlays and 'parlay' in prediction_data:
                old_parlay = prediction_data.get('parlay')
                if old_parlay:
                    parlays = [old_parlay]
                    # 转换为新格式
                    prediction_data['parlays'] = parlays
                    del prediction_data['parlay']

            for parlay in parlays:
                existing_parlay_status = parlay.get('hit_status')
                if not existing_parlay_status or existing_parlay_status == 'None' or existing_parlay_status in ['', None]:
                    parlay['hit_status'] = hit_status

            recommendation.prediction_data = prediction_data

        # 更新状态和结果，并设置归档时间
        recommendation.status = RecommendationStatus.COMPLETED
        recommendation.actual_outcome = actual_outcome
        recommendation.archived_at = datetime.utcnow()  # 设置归档时间，让推荐在历史记录中显示

        db.commit()
        db.refresh(recommendation)

        return recommendation

    @staticmethod
    def get_recommendation_detail(
        db: Session,
        recommendation_id: int
    ) -> Optional[Recommendation]:
        """
        获取历史推荐详情

        Args:
            db: 数据库会话
            recommendation_id: 推荐ID

        Returns:
            推荐对象或None
        """
        return db.query(Recommendation).filter(
            Recommendation.id == recommendation_id,
            Recommendation.status == RecommendationStatus.COMPLETED
        ).first()

    @staticmethod
    def get_monthly_statistics(
        db: Session,
        prediction_type: Optional[str] = None,
        is_paid_user: bool = True
    ) -> list:
        """
        获取按月统计的命中率数据

        Args:
            db: 数据库会话
            prediction_type: 可选的预测类型过滤（football/basketball）
            is_paid_user: 是否为付费用户

        Returns:
            月度统计数据列表，按月份降序排列
        """
        import json
        from collections import defaultdict

        # 构建查询
        query = db.query(Recommendation).filter(
            Recommendation.status == RecommendationStatus.COMPLETED,
            Recommendation.archived_at.isnot(None)
        )

        # 添加预测类型过滤
        if prediction_type:
            query = query.filter(Recommendation.prediction_type == prediction_type)

        recommendations = query.all()

        # 按月统计
        monthly_stats = defaultdict(lambda: {
            'month': '',
            'total_count': 0,
            'hit_count': 0,
            'football_count': 0,
            'football_hit': 0,
            'basketball_count': 0,
            'basketball_hit': 0
        })

        for rec in recommendations:
            if not rec.prediction_data:
                continue

            # 提取月份
            month_key = rec.created_at.strftime('%Y-%m')
            monthly_stats[month_key]['month'] = month_key

            # 解析单场比赛数据
            try:
                data = rec.prediction_data if isinstance(rec.prediction_data, dict) else json.loads(rec.prediction_data)
                single_matches = data.get('single_matches', [])

                for match in single_matches:
                    hit_status = match.get('hit_status')

                    # 只统计有命中状态的比赛
                    if hit_status and hit_status != 'None' and hit_status != '':
                        monthly_stats[month_key]['total_count'] += 1
                        if HistoryService._is_accurate_status(hit_status):
                            monthly_stats[month_key]['hit_count'] += 1

                        # 按运动类型统计
                        if rec.prediction_type == 'football':
                            monthly_stats[month_key]['football_count'] += 1
                            if HistoryService._is_accurate_status(hit_status):
                                monthly_stats[month_key]['football_hit'] += 1
                        elif rec.prediction_type == 'basketball':
                            monthly_stats[month_key]['basketball_count'] += 1
                            if HistoryService._is_accurate_status(hit_status):
                                monthly_stats[month_key]['basketball_hit'] += 1
            except Exception as e:
                logger.error(f"解析prediction_data失败: {e}")
                continue

        # 转换为列表并计算命中率
        result = []
        # 获取当前月份
        current_month = datetime.utcnow().strftime('%Y-%m')

        for month_key in sorted(monthly_stats.keys(), reverse=True):
            # 过滤掉当月的数据
            if month_key == current_month:
                continue

            stats = monthly_stats[month_key]
            if stats['total_count'] > 0:
                hit_rate = round(stats['hit_count'] / stats['total_count'] * 100, 2)
                football_rate = round(stats['football_hit'] / stats['football_count'] * 100, 2) if stats['football_count'] > 0 else 0
                basketball_rate = round(stats['basketball_hit'] / stats['basketball_count'] * 100, 2) if stats['basketball_count'] > 0 else 0

                result.append({
                    'month': stats['month'],
                    'total_count': stats['total_count'],
                    'hit_count': stats['hit_count'],
                    'hit_rate': hit_rate,
                    'football_count': stats['football_count'],
                    'football_hit': stats['football_hit'],
                    'football_rate': football_rate,
                    'basketball_count': stats['basketball_count'],
                    'basketball_hit': stats['basketball_hit'],
                    'basketball_rate': basketball_rate
                })

        return result

    @staticmethod
    def get_highlight_ids(db: Session, limit: int = 10) -> list:
        """
        获取高命中推荐ID列表（用于免费用户预览展示）
        分批查询，避免全量加载到内存
        """
        from app.models.recommendation import Recommendation, RecommendationStatus

        BATCH_SIZE = 200
        offset = 0
        ids = []

        while len(ids) < limit:
            batch = db.query(Recommendation).filter(
                Recommendation.status == RecommendationStatus.COMPLETED,
                Recommendation.archived_at.isnot(None)
            ).order_by(Recommendation.archived_at.desc()).offset(offset).limit(BATCH_SIZE).all()

            if not batch:
                break

            for rec in batch:
                if len(ids) >= limit:
                    break
                if rec.actual_outcome:
                    hit_status = rec.actual_outcome.get('hit_status', '')
                    is_highlight = rec.actual_outcome.get('is_highlight', False)
                    # 入选条件：命中(hit/push) 或 管理员显式标记为精选展示(partial也可)
                    if HistoryService._is_accurate_status(hit_status) or is_highlight:
                        ids.append(rec.id)

            offset += BATCH_SIZE

        return ids
