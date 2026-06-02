"""
机器学习服务
提供K-Means、K-Medoids、OPTICS、AGNES、GMM聚类，线性回归、异常检测、关联规则和时间序列预测
"""
import logging
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
import numpy as np
from sklearn.cluster import KMeans, OPTICS, AgglomerativeClustering
from sklearn.mixture import GaussianMixture
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import IsolationForest
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.metrics import mean_squared_error, r2_score, silhouette_score, calinski_harabasz_score, davies_bouldin_score
from sklearn.decomposition import PCA
from itertools import combinations

logger = logging.getLogger(__name__)


class MLService:
    """机器学习服务类：提供聚类、回归、异常检测等功能"""

    @classmethod
    def kmeans_clustering(
        cls,
        df: pd.DataFrame,
        features: List[str],
        n_clusters: int = 3,
        scale_data: bool = True,
    ) -> Dict[str, Any]:
        """
        K-Means聚类分析

        Args:
            df: DataFrame对象
            features: 特征列名列表
            n_clusters: 聚类数量
            scale_data: 是否标准化

        Returns:
            聚类结果字典
        """
        # 验证特征列
        valid_features = [f for f in features if f in df.columns]
        if len(valid_features) < 2:
            raise ValueError("至少需要2个有效特征列进行聚类")

        # 准备数据
        X = df[valid_features].copy()

        # 处理非数值列
        for col in X.columns:
            if not pd.api.types.is_numeric_dtype(X[col]):
                le = LabelEncoder()
                X[col] = le.fit_transform(X[col].astype(str))

        # 删除缺失值
        X = X.dropna()

        if len(X) < n_clusters:
            raise ValueError(f"有效数据量({len(X)})小于聚类数量({n_clusters})")

        # 标准化
        scaler = StandardScaler() if scale_data else None
        X_scaled = scaler.fit_transform(X) if scale_data else X.values

        # K-Means聚类
        kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        labels = kmeans.fit_predict(X_scaled)

        # 聚类中心（逆标准化）
        centers = kmeans.cluster_centers_
        if scale_data:
            centers = scaler.inverse_transform(centers)

        # 各簇样本数量
        cluster_sizes = {}
        for i in range(n_clusters):
            cluster_sizes[int(i)] = int((labels == i).sum())

        # 轮廓系数
        silhouette = None
        if len(set(labels)) > 1 and n_clusters > 1:
            try:
                # 如果数据量太大，抽样计算轮廓系数
                sample_size = min(5000, len(X_scaled))
                if len(X_scaled) > sample_size:
                    indices = np.random.choice(len(X_scaled), sample_size, replace=False)
                    silhouette = float(silhouette_score(X_scaled[indices], labels[indices]))
                else:
                    silhouette = float(silhouette_score(X_scaled, labels))
            except Exception:
                silhouette = None

        # 使用PCA降维用于可视化（2D散点）
        pca = PCA(n_components=2)
        pca_result = pca.fit_transform(X_scaled)

        scatter_data = {
            "x": pca_result[:, 0].tolist(),
            "y": pca_result[:, 1].tolist(),
            "labels": labels.tolist(),
            "pca_variance_ratio": [round(float(v), 4) for v in pca.explained_variance_ratio_],
        }

        return {
            "n_clusters": n_clusters,
            "cluster_labels": labels.tolist(),
            "cluster_centers": [
                {valid_features[j]: round(float(centers[i][j]), 4) for j in range(len(valid_features))}
                for i in range(n_clusters)
            ],
            "cluster_sizes": cluster_sizes,
            "inertia": round(float(kmeans.inertia_), 4),
            "silhouette_score": round(silhouette, 4) if silhouette else None,
            "features": valid_features,
            "scatter_data": scatter_data,
        }

    @staticmethod
    def _euclidean_cdist(XA, XB):
        """纯 numpy 欧几里得距离矩阵，不依赖 scipy"""
        XA_sq = np.sum(XA**2, axis=1, keepdims=True)  # (n, 1)
        XB_sq = np.sum(XB**2, axis=1, keepdims=True)  # (m, 1)
        dist_sq = XA_sq + XB_sq.T - 2 * np.dot(XA, XB.T)
        dist_sq = np.maximum(dist_sq, 0)
        return np.sqrt(dist_sq)

    @classmethod
    def kmedoids_clustering(
        cls,
        df: pd.DataFrame,
        features: List[str],
        n_clusters: int = 3,
        max_iter: int = 100,
        scale_data: bool = True,
    ) -> Dict[str, Any]:
        """
        K-Medoids (PAM) 聚类分析 — 使用实际数据点作为簇中心，对异常值更鲁棒
        """
        valid_features = [f for f in features if f in df.columns]
        if len(valid_features) < 2:
            raise ValueError("至少需要2个有效特征列进行聚类")

        X = df[valid_features].copy()
        for col in X.columns:
            if not pd.api.types.is_numeric_dtype(X[col]):
                le = LabelEncoder()
                X[col] = le.fit_transform(X[col].astype(str))
        X = X.dropna()

        if len(X) < n_clusters:
            raise ValueError(f"有效数据量({len(X)})小于聚类数量({n_clusters})")

        scaler = StandardScaler() if scale_data else None
        X_scaled = scaler.fit_transform(X) if scale_data else X.values
        n_samples = len(X_scaled)

        # 随机初始化 medoids
        rng = np.random.RandomState(42)
        medoid_indices = rng.choice(n_samples, min(n_clusters, n_samples), replace=False).tolist()
        actual_k = len(medoid_indices)
        labels = np.zeros(n_samples, dtype=int)

        for _iter in range(max_iter):
            distances = cls._euclidean_cdist(X_scaled, X_scaled[medoid_indices])
            new_labels = np.argmin(distances, axis=1)

            new_medoid_indices = []
            for k in range(actual_k):
                cluster_mask = new_labels == k
                if cluster_mask.sum() == 0:
                    new_medoid_indices.append(medoid_indices[k])
                    continue
                cluster_points = X_scaled[cluster_mask]
                cluster_indices = np.where(cluster_mask)[0]
                intra_distances = cls._euclidean_cdist(cluster_points, cluster_points).sum(axis=1)
                best_local_idx = np.argmin(intra_distances)
                new_medoid_indices.append(int(cluster_indices[best_local_idx]))

            if set(new_medoid_indices) == set(medoid_indices):
                labels = new_labels
                break
            medoid_indices = new_medoid_indices
            labels = new_labels

        cluster_sizes = {int(i): int((labels == i).sum()) for i in range(actual_k)}
        silhouette = None
        if actual_k > 1 and len(set(labels)) > 1:
            try:
                sample_size = min(5000, n_samples)
                if n_samples > sample_size:
                    idx_sample = rng.choice(n_samples, sample_size, replace=False)
                    silhouette = float(silhouette_score(X_scaled[idx_sample], labels[idx_sample]))
                else:
                    silhouette = float(silhouette_score(X_scaled, labels))
            except Exception:
                silhouette = None

        calinski = None
        try:
            if actual_k > 1 and len(set(labels)) > 1:
                calinski = float(calinski_harabasz_score(X_scaled, labels))
        except Exception:
            pass

        davies = None
        try:
            if actual_k > 1 and len(set(labels)) > 1:
                davies = float(davies_bouldin_score(X_scaled, labels))
        except Exception:
            pass

        centers_raw = X_scaled[medoid_indices]
        if scale_data:
            centers_raw = scaler.inverse_transform(centers_raw)
        cluster_centers = [
            {valid_features[j]: round(float(centers_raw[i][j]), 4) for j in range(len(valid_features))}
            for i in range(actual_k)
        ]

        pca = PCA(n_components=2)
        pca_result = pca.fit_transform(X_scaled)
        scatter_data = {
            "x": pca_result[:, 0].tolist(),
            "y": pca_result[:, 1].tolist(),
            "labels": labels.tolist(),
            "pca_variance_ratio": [round(float(v), 4) for v in pca.explained_variance_ratio_],
        }

        total_distance = float(cls._euclidean_cdist(X_scaled, X_scaled[medoid_indices]).min(axis=1).sum())

        return {
            "algorithm": "K-Medoids (PAM)",
            "n_clusters": actual_k,
            "cluster_labels": labels.tolist(),
            "cluster_centers": cluster_centers,
            "cluster_sizes": cluster_sizes,
            "silhouette_score": round(silhouette, 4) if silhouette else None,
            "calinski_harabasz_score": round(calinski, 4) if calinski else None,
            "davies_bouldin_score": round(davies, 4) if davies else None,
            "total_distance": round(total_distance, 4),
            "features": valid_features,
            "scatter_data": scatter_data,
        }

    @classmethod
    def optics_clustering(
        cls,
        df: pd.DataFrame,
        features: List[str],
        min_samples: int = 5,
        xi: float = 0.05,
        scale_data: bool = True,
    ) -> Dict[str, Any]:
        """
        OPTICS 聚类分析 — 基于密度的聚类，自动发现不同密度的簇

        Args:
            df: DataFrame对象
            features: 特征列名列表
            min_samples: 最小样本数
            xi: 簇提取阈值
            scale_data: 是否标准化

        Returns:
            聚类结果字典
        """
        valid_features = [f for f in features if f in df.columns]
        if len(valid_features) < 2:
            raise ValueError("至少需要2个有效特征列进行聚类")

        X = df[valid_features].copy()
        for col in X.columns:
            if not pd.api.types.is_numeric_dtype(X[col]):
                le = LabelEncoder()
                X[col] = le.fit_transform(X[col].astype(str))
        X = X.dropna()

        if len(X) < min_samples:
            raise ValueError(f"有效数据量({len(X)})小于最小样本数({min_samples})")

        scaler = StandardScaler() if scale_data else None
        X_scaled = scaler.fit_transform(X) if scale_data else X.values

        optics = OPTICS(min_samples=min_samples, xi=xi, min_cluster_size=min_samples)
        labels = optics.fit_predict(X_scaled)

        # OPTICS 标签中 -1 表示噪声
        unique_labels = set(labels)
        n_clusters = len(unique_labels - {-1})
        n_noise = int((labels == -1).sum())

        cluster_sizes = {}
        for lb in unique_labels:
            cluster_sizes[int(lb)] = int((labels == lb).sum())

        silhouette = None
        calinski = None
        davies = None
        if n_clusters > 1:
            non_noise_mask = labels != -1
            if non_noise_mask.sum() > n_clusters * 2:
                try:
                    silhouette = float(silhouette_score(X_scaled[non_noise_mask], labels[non_noise_mask]))
                except Exception:
                    pass
                try:
                    calinski = float(calinski_harabasz_score(X_scaled[non_noise_mask], labels[non_noise_mask]))
                except Exception:
                    pass
                try:
                    davies = float(davies_bouldin_score(X_scaled[non_noise_mask], labels[non_noise_mask]))
                except Exception:
                    pass

        # 每簇中心
        cluster_centers = []
        for lb in sorted(unique_labels):
            if lb == -1:
                continue
            mask = labels == lb
            center = X_scaled[mask].mean(axis=0)
            if scale_data:
                center = scaler.inverse_transform(center.reshape(1, -1))[0]
            cluster_centers.append({
                "cluster": int(lb),
                **{valid_features[j]: round(float(center[j]), 4) for j in range(len(valid_features))}
            })

        pca = PCA(n_components=2)
        pca_result = pca.fit_transform(X_scaled)
        scatter_data = {
            "x": pca_result[:, 0].tolist(),
            "y": pca_result[:, 1].tolist(),
            "labels": labels.tolist(),
            "pca_variance_ratio": [round(float(v), 4) for v in pca.explained_variance_ratio_],
        }

        reachability = optics.reachability_.tolist() if hasattr(optics, 'reachability_') and optics.reachability_ is not None else []
        ordering = optics.ordering_.tolist() if hasattr(optics, 'ordering_') and optics.ordering_ is not None else []

        return {
            "algorithm": "OPTICS",
            "n_clusters": n_clusters,
            "n_noise": n_noise,
            "cluster_labels": labels.tolist(),
            "cluster_centers": cluster_centers,
            "cluster_sizes": cluster_sizes,
            "silhouette_score": round(silhouette, 4) if silhouette else None,
            "calinski_harabasz_score": round(calinski, 4) if calinski else None,
            "davies_bouldin_score": round(davies, 4) if davies else None,
            "parameters": {"min_samples": min_samples, "xi": xi},
            "features": valid_features,
            "scatter_data": scatter_data,
        }

    @classmethod
    def agnes_clustering(
        cls,
        df: pd.DataFrame,
        features: List[str],
        n_clusters: int = 3,
        linkage: str = "ward",
        scale_data: bool = True,
    ) -> Dict[str, Any]:
        """
        AGNES (Agglomerative Nesting) 层次聚类 — 自底向上合并

        Args:
            df: DataFrame对象
            features: 特征列名列表
            n_clusters: 聚类数量
            linkage: 链接方式 (ward/complete/average/single)
            scale_data: 是否标准化

        Returns:
            聚类结果字典
        """
        valid_features = [f for f in features if f in df.columns]
        if len(valid_features) < 2:
            raise ValueError("至少需要2个有效特征列进行聚类")

        X = df[valid_features].copy()
        for col in X.columns:
            if not pd.api.types.is_numeric_dtype(X[col]):
                le = LabelEncoder()
                X[col] = le.fit_transform(X[col].astype(str))
        X = X.dropna()

        if len(X) < n_clusters:
            raise ValueError(f"有效数据量({len(X)})小于聚类数量({n_clusters})")

        scaler = StandardScaler() if scale_data else None
        X_scaled = scaler.fit_transform(X) if scale_data else X.values

        agnes = AgglomerativeClustering(n_clusters=n_clusters, linkage=linkage)
        labels = agnes.fit_predict(X_scaled)

        cluster_sizes = {int(i): int((labels == i).sum()) for i in range(n_clusters)}

        silhouette = None
        calinski = None
        davies = None
        if n_clusters > 1 and len(set(labels)) > 1:
            try:
                silhouette = float(silhouette_score(X_scaled, labels))
            except Exception:
                pass
            try:
                calinski = float(calinski_harabasz_score(X_scaled, labels))
            except Exception:
                pass
            try:
                davies = float(davies_bouldin_score(X_scaled, labels))
            except Exception:
                pass

        cluster_centers = []
        for i in range(n_clusters):
            mask = labels == i
            center = X_scaled[mask].mean(axis=0)
            if scale_data:
                center = scaler.inverse_transform(center.reshape(1, -1))[0]
            cluster_centers.append({
                **{valid_features[j]: round(float(center[j]), 4) for j in range(len(valid_features))}
            })

        pca = PCA(n_components=2)
        pca_result = pca.fit_transform(X_scaled)
        scatter_data = {
            "x": pca_result[:, 0].tolist(),
            "y": pca_result[:, 1].tolist(),
            "labels": labels.tolist(),
            "pca_variance_ratio": [round(float(v), 4) for v in pca.explained_variance_ratio_],
        }

        return {
            "algorithm": f"AGNES ({linkage})",
            "n_clusters": n_clusters,
            "linkage": linkage,
            "cluster_labels": labels.tolist(),
            "cluster_centers": cluster_centers,
            "cluster_sizes": cluster_sizes,
            "silhouette_score": round(silhouette, 4) if silhouette else None,
            "calinski_harabasz_score": round(calinski, 4) if calinski else None,
            "davies_bouldin_score": round(davies, 4) if davies else None,
            "features": valid_features,
            "scatter_data": scatter_data,
        }

    @classmethod
    def gmm_clustering(
        cls,
        df: pd.DataFrame,
        features: List[str],
        n_components: int = 3,
        covariance_type: str = "full",
        scale_data: bool = True,
    ) -> Dict[str, Any]:
        """
        高斯混合模型 (GMM) 聚类 — 软聚类，概率分配

        Args:
            df: DataFrame对象
            features: 特征列名列表
            n_components: 高斯成分数量
            covariance_type: 协方差类型 (full/tied/diag/spherical)
            scale_data: 是否标准化

        Returns:
            聚类结果字典
        """
        valid_features = [f for f in features if f in df.columns]
        if len(valid_features) < 2:
            raise ValueError("至少需要2个有效特征列进行聚类")

        X = df[valid_features].copy()
        for col in X.columns:
            if not pd.api.types.is_numeric_dtype(X[col]):
                le = LabelEncoder()
                X[col] = le.fit_transform(X[col].astype(str))
        X = X.dropna()

        if len(X) < n_components:
            raise ValueError(f"有效数据量({len(X)})小于成分数({n_components})")

        scaler = StandardScaler() if scale_data else None
        X_scaled = scaler.fit_transform(X) if scale_data else X.values

        gmm = GaussianMixture(n_components=n_components, covariance_type=covariance_type, random_state=42)
        labels = gmm.fit_predict(X_scaled)
        probabilities = gmm.predict_proba(X_scaled)

        cluster_sizes = {int(i): int((labels == i).sum()) for i in range(n_components)}

        silhouette = None
        calinski = None
        davies = None
        if n_components > 1 and len(set(labels)) > 1:
            try:
                silhouette = float(silhouette_score(X_scaled, labels))
            except Exception:
                pass
            try:
                calinski = float(calinski_harabasz_score(X_scaled, labels))
            except Exception:
                pass
            try:
                davies = float(davies_bouldin_score(X_scaled, labels))
            except Exception:
                pass

        # GMM 均值作为簇中心
        centers = gmm.means_
        if scale_data:
            centers = scaler.inverse_transform(centers)
        cluster_centers = [
            {valid_features[j]: round(float(centers[i][j]), 4) for j in range(len(valid_features))}
            for i in range(n_components)
        ]

        # 权重
        weights = [round(float(w), 4) for w in gmm.weights_]

        pca = PCA(n_components=2)
        pca_result = pca.fit_transform(X_scaled)
        scatter_data = {
            "x": pca_result[:, 0].tolist(),
            "y": pca_result[:, 1].tolist(),
            "labels": labels.tolist(),
            "pca_variance_ratio": [round(float(v), 4) for v in pca.explained_variance_ratio_],
        }

        return {
            "algorithm": f"GMM ({covariance_type})",
            "n_components": n_components,
            "covariance_type": covariance_type,
            "cluster_labels": labels.tolist(),
            "cluster_centers": cluster_centers,
            "cluster_sizes": cluster_sizes,
            "silhouette_score": round(silhouette, 4) if silhouette else None,
            "calinski_harabasz_score": round(calinski, 4) if calinski else None,
            "davies_bouldin_score": round(davies, 4) if davies else None,
            "bic": round(float(gmm.bic(X_scaled)), 4),
            "aic": round(float(gmm.aic(X_scaled)), 4),
            "weights": weights,
            "features": valid_features,
            "scatter_data": scatter_data,
        }

    @classmethod
    def multi_clustering(
        cls,
        df: pd.DataFrame,
        features: List[str],
        algorithms: List[str],
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        多算法聚类对比 — 运行选择的多种聚类算法并横向对比

        Args:
            df: DataFrame对象
            features: 特征列名列表
            algorithms: 算法列表 (kmeans/kmedoids/optics/agnes/gmm)
            params: 各算法参数

        Returns:
            对比结果
        """
        params = params or {}
        results = {}
        comparison = []

        algo_map = {
            "kmeans": ("K-Means", cls.kmeans_clustering),
            "kmedoids": ("K-Medoids (PAM)", cls.kmedoids_clustering),
            "optics": ("OPTICS", cls.optics_clustering),
            "agnes": ("AGNES 层次聚类", cls.agnes_clustering),
            "gmm": ("GMM 高斯混合", cls.gmm_clustering),
        }

        for algo_key in algorithms:
            if algo_key not in algo_map:
                continue
            algo_name, algo_func = algo_map[algo_key]
            try:
                algo_params = params.get(algo_key, {})
                # 为不同算法设置默认参数
                if algo_key == "kmeans":
                    algo_params.setdefault("n_clusters", params.get("n_clusters", 3))
                elif algo_key == "kmedoids":
                    algo_params.setdefault("n_clusters", params.get("n_clusters", 3))
                elif algo_key == "optics":
                    algo_params.setdefault("min_samples", 5)
                elif algo_key == "agnes":
                    algo_params.setdefault("n_clusters", params.get("n_clusters", 3))
                    algo_params.setdefault("linkage", "ward")
                elif algo_key == "gmm":
                    algo_params.setdefault("n_components", algo_params.pop("n_clusters", params.get("n_clusters", 3)))
                    algo_params.setdefault("covariance_type", "full")
                    algo_params.pop("n_clusters", None)  # 移除不被 GMM 接受的参数

                result = algo_func(df, features, **algo_params)
                results[algo_key] = result

                # 构建对比行
                row = {
                    "algorithm": algo_name,
                    "key": algo_key,
                    "n_clusters": result.get("n_clusters", result.get("n_components", "auto")),
                    "silhouette_score": result.get("silhouette_score"),
                    "calinski_harabasz_score": result.get("calinski_harabasz_score"),
                    "davies_bouldin_score": result.get("davies_bouldin_score"),
                }
                # 算法特有指标
                if algo_key == "kmeans":
                    row["inertia"] = result.get("inertia")
                elif algo_key == "kmedoids":
                    row["total_distance"] = result.get("total_distance")
                elif algo_key == "optics":
                    row["n_noise"] = result.get("n_noise")
                elif algo_key == "gmm":
                    row["bic"] = result.get("bic")
                    row["aic"] = result.get("aic")
                comparison.append(row)
            except Exception as e:
                logger.warning(f"算法 {algo_name} 执行失败: {str(e)}")
                comparison.append({
                    "algorithm": algo_name,
                    "key": algo_key,
                    "error": str(e),
                })

        # 评估总结
        best_silhouette = None
        best_calinski = None
        best_davies = None  # Davies-Bouldin 越小越好
        for c in comparison:
            if c.get("silhouette_score") is not None:
                if best_silhouette is None or c["silhouette_score"] > comparison[best_silhouette].get("silhouette_score", -1):
                    best_silhouette = comparison.index(c)
            if c.get("calinski_harabasz_score") is not None:
                if best_calinski is None or c["calinski_harabasz_score"] > comparison[best_calinski].get("calinski_harabasz_score", -1):
                    best_calinski = comparison.index(c)
            if c.get("davies_bouldin_score") is not None:
                if best_davies is None or c["davies_bouldin_score"] < comparison[best_davies].get("davies_bouldin_score", float('inf')):
                    best_davies = comparison.index(c)

        return {
            "algorithms_run": algorithms,
            "comparison": comparison,
            "results": results,
            "features": features,
            "best_by_silhouette": comparison[best_silhouette]["algorithm"] if best_silhouette is not None else None,
            "best_by_calinski_harabasz": comparison[best_calinski]["algorithm"] if best_calinski is not None else None,
            "best_by_davies_bouldin": comparison[best_davies]["algorithm"] if best_davies is not None else None,
        }

    @classmethod
    def linear_regression(
        cls,
        df: pd.DataFrame,
        features: List[str],
        target: str,
        test_size: float = 0.2,
    ) -> Dict[str, Any]:
        """
        多元线性回归分析

        Args:
            df: DataFrame对象
            features: 特征列名列表
            target: 目标列名
            test_size: 测试集比例

        Returns:
            回归结果字典
        """
        # 验证
        if target not in df.columns:
            raise ValueError(f"目标列 '{target}' 不存在")

        valid_features = [f for f in features if f in df.columns and f != target]
        if not valid_features:
            raise ValueError("没有有效的特征列")

        # 准备数据
        data = df[valid_features + [target]].copy()

        # 处理分类变量
        for col in data.columns:
            if not pd.api.types.is_numeric_dtype(data[col]):
                le = LabelEncoder()
                data[col] = le.fit_transform(data[col].astype(str))

        data = data.dropna()

        if len(data) < 10:
            raise ValueError(f"有效数据量({len(data)})不足以进行回归分析")

        X = data[valid_features].values
        y = data[target].values

        # 划分训练集和测试集
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=42
        )

        # 标准化
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_test_scaled = scaler.transform(X_test)

        # 训练模型
        model = LinearRegression()
        model.fit(X_train_scaled, y_train)

        # 预测
        y_pred = model.predict(X_test_scaled)
        y_train_pred = model.predict(X_train_scaled)

        # 评估指标
        r2 = float(r2_score(y_test, y_pred))
        mse = float(mean_squared_error(y_test, y_pred))
        rmse = float(np.sqrt(mse))
        train_r2 = float(r2_score(y_train, y_train_pred))

        # 系数
        coefficients = {}
        for i, feat in enumerate(valid_features):
            coefficients[feat] = round(float(model.coef_[i]), 6)

        # 特征重要性（基于标准化系数绝对值）
        total = sum(abs(v) for v in coefficients.values())
        feature_importance = {}
        for feat, coef in coefficients.items():
            feature_importance[feat] = round(abs(coef) / max(total, 1e-10), 4)

        return {
            "coefficients": coefficients,
            "intercept": round(float(model.intercept_), 6),
            "r2_score": r2,
            "mse": round(mse, 4),
            "rmse": round(rmse, 4),
            "train_r2": train_r2,
            "predictions": [round(float(p), 4) for p in y_pred.tolist()],
            "actual": [round(float(a), 4) for a in y_test.tolist()],
            "feature_importance": feature_importance,
            "features": valid_features,
            "target": target,
            "train_size": len(X_train),
            "test_size": len(X_test),
        }

    @classmethod
    def anomaly_detection(
        cls,
        df: pd.DataFrame,
        features: Optional[List[str]] = None,
        contamination: float = 0.1,
    ) -> Dict[str, Any]:
        """
        使用Isolation Forest进行异常检测

        Args:
            df: DataFrame对象
            features: 特征列（None表示所有数值列）
            contamination: 预期异常比例

        Returns:
            异常检测结果（含异常行完整数据）
        """
        if features is None:
            features = df.select_dtypes(include=[np.number]).columns.tolist()

        valid_features = [f for f in features if f in df.columns]
        data = df[valid_features].copy()

        # 处理非数值列
        for col in data.columns:
            if not pd.api.types.is_numeric_dtype(data[col]):
                le = LabelEncoder()
                data[col] = le.fit_transform(data[col].astype(str))

        # 保留原始行索引
        original_indices = data.index.tolist()
        data = data.dropna()
        # 更新索引映射
        clean_indices = data.index.tolist()

        if len(data) < 10:
            return {"error": "数据量不足", "anomalies": [], "anomaly_count": 0}

        # Isolation Forest
        model = IsolationForest(
            contamination=contamination,
            random_state=42,
            n_estimators=100,
        )
        predictions = model.fit_predict(data.values)

        # -1 表示异常，1 表示正常
        anomaly_mask = predictions == -1
        anomaly_positions = np.where(anomaly_mask)[0].tolist()
        anomaly_indices = [clean_indices[i] for i in anomaly_positions]
        anomaly_scores = model.decision_function(data.values)
        normalized_scores = (-anomaly_scores + anomaly_scores.max()) / (
            anomaly_scores.max() - anomaly_scores.min() + 1e-10
        )

        # 构建每列的 IQR 异常范围
        col_iqr_bounds = {}
        for col in valid_features:
            col_data = data[col]
            if pd.api.types.is_numeric_dtype(col_data):
                Q1 = float(col_data.quantile(0.25))
                Q3 = float(col_data.quantile(0.75))
                IQR = Q3 - Q1
                lower = Q1 - 1.5 * IQR
                upper = Q3 + 1.5 * IQR
                col_iqr_bounds[col] = {"Q1": round(Q1, 4), "Q3": round(Q3, 4), "IQR": round(IQR, 4), "lower": round(lower, 4), "upper": round(upper, 4)}

        # 构建异常行详情（限前100条）
        anomaly_rows = []
        all_columns = df.columns.tolist()
        for i, pos in enumerate(anomaly_positions[:100]):
            orig_idx = clean_indices[pos]
            row_data = {}
            # 获取原始 df 中该行的所有列数据
            for col in all_columns:
                val = df.loc[orig_idx, col]
                if hasattr(val, 'item'):
                    val = val.item()
                elif isinstance(val, float) and (pd.isna(val) or np.isinf(val)):
                    val = None
                row_data[col] = val

            # 找出该行中哪些值在 IQR 范围外
            outlier_columns = []
            for col in valid_features:
                if col in col_iqr_bounds:
                    v = data.loc[orig_idx, col]
                    bounds = col_iqr_bounds[col]
                    if pd.notna(v) and (v < bounds["lower"] or v > bounds["upper"]):
                        outlier_columns.append({
                            "column": col,
                            "value": round(float(v), 4) if not (isinstance(v, float) and np.isnan(v)) else None,
                            "lower_bound": bounds["lower"],
                            "upper_bound": bounds["upper"],
                        })

            anomaly_rows.append({
                "index": int(orig_idx),
                "score": round(float(normalized_scores[pos]), 4),
                "data": row_data,
                "outlier_columns": outlier_columns,
            })

        return {
            "anomaly_indices": [int(x) for x in anomaly_indices],
            "anomaly_count": len(anomaly_indices),
            "total_samples": len(data),
            "anomaly_ratio": round(len(anomaly_indices) / len(data) * 100, 2),
            "anomaly_scores": [round(float(s), 4) for s in normalized_scores.tolist()],
            "predictions": predictions.tolist(),
            "features": valid_features,
            "anomaly_rows": anomaly_rows,
            "col_iqr_bounds": col_iqr_bounds,
        }

    @classmethod
    def apriori_association(
        cls,
        df: pd.DataFrame,
        columns: List[str],
        min_support: float = 0.1,
        min_confidence: float = 0.5,
    ) -> Dict[str, Any]:
        """
        简易Apriori关联规则挖掘

        Args:
            df: DataFrame对象
            columns: 参与分析的分类列
            min_support: 最小支持度
            min_confidence: 最小置信度

        Returns:
            关联规则列表
        """
        rules = []
        valid_cols = [c for c in columns if c in df.columns]

        for col in valid_cols:
            value_counts = df[col].value_counts()
            total = len(df)
            for val, count in value_counts.items():
                support = count / total
                if support >= min_support:
                    rules.append({
                        "antecedent": f"{col}={val}",
                        "consequent": None,
                        "support": round(support, 4),
                        "confidence": 1.0,
                        "lift": 1.0,
                    })

        # 挖掘两列之间的关联
        for col1, col2 in combinations(valid_cols, 2):
            for val1 in df[col1].unique()[:10]:  # 限制值数量
                for val2 in df[col2].unique()[:10]:
                    if pd.isna(val1) or pd.isna(val2):
                        continue
                    mask1 = df[col1] == val1
                    mask2 = df[col2] == val2
                    mask_both = mask1 & mask2

                    support_both = mask_both.sum() / len(df)
                    support_ante = mask1.sum() / len(df)

                    if support_both >= min_support and support_ante > 0:
                        confidence = support_both / support_ante
                        support_cons = mask2.sum() / len(df)
                        lift = support_both / (support_ante * support_cons) if support_ante * support_cons > 0 else 0

                        if confidence >= min_confidence:
                            rules.append({
                                "antecedent": f"{col1}={val1}",
                                "consequent": f"{col2}={val2}",
                                "support": round(support_both, 4),
                                "confidence": round(confidence, 4),
                                "lift": round(lift, 4),
                            })

        return {
            "rules": sorted(rules, key=lambda r: r.get("lift", 0) or 0, reverse=True)[:50],
            "total_rules": len(rules),
            "parameters": {
                "min_support": min_support,
                "min_confidence": min_confidence,
            },
        }

    @classmethod
    def time_series_forecast(
        cls,
        df: pd.DataFrame,
        date_column: str,
        value_column: str,
        periods: int = 5,
    ) -> Dict[str, Any]:
        """
        简易时间序列预测（使用移动平均+趋势外推）

        Args:
            df: DataFrame对象
            date_column: 日期列
            value_column: 数值列
            periods: 预测期数

        Returns:
            预测结果
        """
        df_ts = df.copy()
        df_ts[date_column] = pd.to_datetime(df_ts[date_column], errors="coerce")
        df_ts = df_ts.dropna(subset=[date_column, value_column])
        df_ts = df_ts.sort_values(date_column)

        values = df_ts[value_column].values.astype(float)

        if len(values) < 4:
            return {"error": "数据量不足，至少需要4个数据点"}

        # 简易趋势预测：线性回归 + 移动平均
        x = np.arange(len(values)).reshape(-1, 1)
        model = LinearRegression()
        model.fit(x, values)

        # 预测
        future_x = np.arange(len(values), len(values) + periods).reshape(-1, 1)
        forecast = model.predict(future_x)

        # 计算趋势强度
        trend_strength = float(model.coef_[0])
        trend_direction = "上升" if trend_strength > 0 else "下降"

        # 置信区间（基于历史误差的简化版本）
        residuals = values - model.predict(x)
        std_residuals = np.std(residuals)
        lower_bound = forecast - 1.96 * std_residuals
        upper_bound = forecast + 1.96 * std_residuals

        return {
            "historical_dates": df_ts[date_column].dt.strftime("%Y-%m-%d").tolist(),
            "historical_values": values.tolist(),
            "forecast_values": [round(float(f), 2) for f in forecast.tolist()],
            "forecast_lower": [round(float(l), 2) for l in lower_bound.tolist()],
            "forecast_upper": [round(float(u), 2) for u in upper_bound.tolist()],
            "trend_direction": trend_direction,
            "trend_strength": round(trend_strength, 4),
            "periods": periods,
        }
