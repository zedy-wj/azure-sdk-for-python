# -------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# --------------------------------------------------------------------------

from typing import Any, Dict, List, Optional, Tuple, TYPE_CHECKING, Union
from urllib.parse import quote, urlparse

from azure.core import MatchConditions
from azure.core.pipeline.transport import HttpRequest
from ._blob_client_helpers import _generic_delete_blob_options
from ._generated import AzureBlobStorage
from ._models import BlobProperties
from ._shared.base_client import parse_query

if TYPE_CHECKING:
    from azure.storage.blob import RehydratePriority
    from urllib.parse import ParseResult
    from ._generated.models import LeaseAccessConditions, ModifiedAccessConditions
    from ._models import PremiumPageBlobTier, StandardBlobTier


def _parse_url(
    account_url: str,
    container_name: str,
) -> Tuple["ParseResult", Any]:
    """Performs initial input validation and returns the parsed URL and SAS token.
    :param str account_url: The URL to the storage account.
    :param str container_name: The name of the container.
    :returns: The parsed URL and SAS token.
    :rtype: Tuple[ParseResult, Any]
    """
    try:
        if not account_url.lower().startswith('http'):
            account_url = "https://" + account_url
    except AttributeError as exc:
        raise ValueError("Container URL must be a string.") from exc
    parsed_url = urlparse(account_url.rstrip('/'))
    if not container_name:
        raise ValueError("Please specify a container name.")
    if not parsed_url.netloc:
        raise ValueError(f"Invalid URL: {account_url}")

    _, sas_token = parse_query(parsed_url.query)

    return parsed_url, sas_token

def _format_url(container_name: Union[bytes, str], hostname: str, scheme: str, query_str: str) -> str:
    """Format the endpoint URL according to the current location mode hostname.

    :param Union[bytes, str] container_name:
        The name of the container.
    :param str hostname:
        The current location mode hostname.
    :param str scheme:
        The scheme for the current location mode hostname.
    :param str query_str:
        The query string of the endpoint URL being formatted.
    :returns: The formatted endpoint URL according to the specified location mode hostname.
    :rtype: str
    """
    if isinstance(container_name, str):
        container_name = container_name.encode('UTF-8')
    return f"{scheme}://{hostname}/{quote(container_name)}{query_str}"

# This code is a copy from _generated.
# Once Autorest is able to provide request preparation this code should be removed.
def _generate_delete_blobs_subrequest_options(
    client: AzureBlobStorage,
    snapshot: Optional[str] = None,
    version_id: Optional[str] = None,
    delete_snapshots: Optional[str] = None,
    lease_access_conditions: Optional["LeaseAccessConditions"] = None,
    modified_access_conditions: Optional["ModifiedAccessConditions"] = None,
    **kwargs
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """Creates a dictionary containing the options for a delete blob sub-request operation.

    :param AzureBlobStorage client:
        The generated Blob Storage client.
    :param Optional[str] snapshot:
        The snapshot data of the blob.
    :param Optional[str] version_id:
        The version id parameter is a value that, when present, specifies the version of the blob to delete.
    :param Optional[str] delete_snapshots:
        Required if the blob has associated snapshots. Values include:
         - "only": Deletes only the blobs snapshots.
         - "include": Deletes the blob along with all snapshots.
    :param lease_access_conditions:
        The access conditions associated with the lease.
    :type lease_access_conditions: Optional[LeaseAccessConditions]
    :param modified_access_conditions:
        The modified access conditions associated with the lease.
    :type modified_access_conditions: Optional[LeaseAccessConditions]
    :returns: A dictionary containing the delete blobs sub-request options.
    :rtype: Tuple[Dict[str, Any], Dict[str, Any]]
    """
    lease_id = None
    if lease_access_conditions is not None:
        lease_id = lease_access_conditions.lease_id
    if_modified_since = None
    if modified_access_conditions is not None:
        if_modified_since = modified_access_conditions.if_modified_since
    if_unmodified_since = None
    if modified_access_conditions is not None:
        if_unmodified_since = modified_access_conditions.if_unmodified_since
    if_match = None
    if modified_access_conditions is not None:
        if_match = modified_access_conditions.if_match
    if_none_match = None
    if modified_access_conditions is not None:
        if_none_match = modified_access_conditions.if_none_match
    if_tags = None
    if modified_access_conditions is not None:
        if_tags = modified_access_conditions.if_tags

    # Construct parameters
    timeout = kwargs.pop('timeout', None)
    query_parameters = {}
    if snapshot is not None:
        query_parameters['snapshot'] = client._serialize.query("snapshot", snapshot, 'str')  # pylint: disable=protected-access
    if version_id is not None:
        query_parameters['versionid'] = client._serialize.query("version_id", version_id, 'str')  # pylint: disable=protected-access
    if timeout is not None:
        query_parameters['timeout'] = client._serialize.query("timeout", timeout, 'int', minimum=0)  # pylint: disable=protected-access

    # Construct headers
    header_parameters = {}
    if delete_snapshots is not None:
        header_parameters['x-ms-delete-snapshots'] = client._serialize.header(  # pylint: disable=protected-access
            "delete_snapshots", delete_snapshots, 'DeleteSnapshotsOptionType')
    if lease_id is not None:
        header_parameters['x-ms-lease-id'] = client._serialize.header(  # pylint: disable=protected-access
            "lease_id", lease_id, 'str')
    if if_modified_since is not None:
        header_parameters['If-Modified-Since'] = client._serialize.header(  # pylint: disable=protected-access
            "if_modified_since", if_modified_since, 'rfc-1123')
    if if_unmodified_since is not None:
        header_parameters['If-Unmodified-Since'] = client._serialize.header(  # pylint: disable=protected-access
            "if_unmodified_since", if_unmodified_since, 'rfc-1123')
    if if_match is not None:
        header_parameters['If-Match'] = client._serialize.header(  # pylint: disable=protected-access
            "if_match", if_match, 'str')
    if if_none_match is not None:
        header_parameters['If-None-Match'] = client._serialize.header(  # pylint: disable=protected-access
            "if_none_match", if_none_match, 'str')
    if if_tags is not None:
        header_parameters['x-ms-if-tags'] = client._serialize.header("if_tags", if_tags, 'str')  # pylint: disable=protected-access

    return query_parameters, header_parameters

def _generate_delete_blobs_options(
    query_str: str,
    container_name: str,
    client: AzureBlobStorage,
    *blobs: Union[str, Dict[str, Any], BlobProperties],
    **kwargs: Any
) -> Tuple[List[HttpRequest], Dict[str, Any]]:
    """Creates a dictionary containing the options for a delete blob operation.

    :param str query_str:
        The query string of the endpoint URL.
    :param str container_name:
        The name of the container.
    :param AzureBlobStorage client:
        The generated Blob Storage client.
    :param blobs:
            The blobs to delete. This can be a single blob, or multiple values can
            be supplied, where each value is either the name of the blob (str) or BlobProperties.

            .. note::
                When the blob type is dict, here's a list of keys, value rules.

                blob name:
                    key: 'name', value type: str
                snapshot you want to delete:
                    key: 'snapshot', value type: str
                version id:
                    key: 'version_id', value type: str
                whether to delete snapshots when deleting blob:
                    key: 'delete_snapshots', value: 'include' or 'only'
                if the blob modified or not:
                    key: 'if_modified_since', 'if_unmodified_since', value type: datetime
                etag:
                    key: 'etag', value type: str
                match the etag or not:
                    key: 'match_condition', value type: MatchConditions
                tags match condition:
                    key: 'if_tags_match_condition', value type: str
                lease:
                    key: 'lease_id', value type: Union[str, LeaseClient]
                timeout for subrequest:
                    key: 'timeout', value type: int

    :type blobs: Union[str, Dict[str, Any], BlobProperties]
    :returns: A tuple containing the list of HttpRequests and the delete blobs options.
    :rtype: Tuple[List[HttpRequest], Dict[str, Any]]
    """
    timeout = kwargs.pop('timeout', None)
    raise_on_any_failure = kwargs.pop('raise_on_any_failure', True)
    delete_snapshots = kwargs.pop('delete_snapshots', None)
    if_modified_since = kwargs.pop('if_modified_since', None)
    if_unmodified_since = kwargs.pop('if_unmodified_since', None)
    if_tags_match_condition = kwargs.pop('if_tags_match_condition', None)
    kwargs.update({'raise_on_any_failure': raise_on_any_failure,
                    'sas': query_str.replace('?', '&'),
                    'timeout': '&timeout=' + str(timeout) if timeout else "",
                    'path': container_name,
                    'restype': 'restype=container&'
                    })

    reqs = []
    for blob in blobs:
        if not isinstance(blob, str):
            blob_name = blob.get('name')
            options = _generic_delete_blob_options(  # pylint: disable=protected-access
                snapshot=blob.get('snapshot'),
                version_id=blob.get('version_id'),
                delete_snapshots=delete_snapshots or blob.get('delete_snapshots'),
                lease=blob.get('lease_id'),
                if_modified_since=if_modified_since or blob.get('if_modified_since'),
                if_unmodified_since=if_unmodified_since or blob.get('if_unmodified_since'),
                etag=blob.get('etag'),
                if_tags_match_condition=if_tags_match_condition or blob.get('if_tags_match_condition'),
                match_condition=blob.get('match_condition') or MatchConditions.IfNotModified if blob.get('etag')
                else None,
                timeout=blob.get('timeout'),
            )
        else:
            blob_name = blob
            options = _generic_delete_blob_options(  # pylint: disable=protected-access
                delete_snapshots=delete_snapshots,
                if_modified_since=if_modified_since,
                if_unmodified_since=if_unmodified_since,
                if_tags_match_condition=if_tags_match_condition
            )

        query_parameters, header_parameters = _generate_delete_blobs_subrequest_options(client, **options)

        req = HttpRequest(
            "DELETE",
            f"/{quote(container_name)}/{quote(str(blob_name), safe='/~')}{query_str}",
            headers=header_parameters
        )
        req.format_parameters(query_parameters)
        reqs.append(req)

    return reqs, kwargs

# This code is a copy from _generated.
# Once Autorest is able to provide request preparation this code should be removed.
def _generate_set_tiers_subrequest_options(
    client: AzureBlobStorage,
    tier: Optional[Union["PremiumPageBlobTier", "StandardBlobTier", str]],
    snapshot: Optional[str] = None,
    version_id: Optional[str] = None,
    rehydrate_priority: Optional["RehydratePriority"] = None,
    lease_access_conditions: Optional["LeaseAccessConditions"] = None,
    **kwargs: Any
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """Creates a dictionary containing the options for a set tiers sub-request operation.

    :param AzureBlobStorage client:
        The generated Blob Storage client.
    :param tier:
        Indicates the tier to be set on the blobs.
    :type tier: Optional[Union["PremiumPageBlobTier", "StandardBlobTier", str]]
    :param Optional[str] snapshot:
        The snapshot data of the blob.
    :param Optional[str] version_id:
        The version id parameter is a value that, when present, specifies the version of the blob to delete.
    :param Optional[RehydratePriority] rehydrate_priority:
        Indicates the priority with which to rehydrate an archived blob.
    :param lease_access_conditions:
        The access conditions associated with the lease.
    :type lease_access_conditions: Optional[LeaseAccessConditions]
    :returns: A dictionary containing the set tiers sub-request options.
    :rtype: Dict[str, Any]
    """
    if not tier:
        raise ValueError("A blob tier must be specified")
    if snapshot and version_id:
        raise ValueError("Snapshot and version_id cannot be set at the same time")
    if_tags = kwargs.pop('if_tags', None)

    lease_id = None
    if lease_access_conditions is not None:
        lease_id = lease_access_conditions.lease_id

    comp = "tier"
    timeout = kwargs.pop('timeout', None)
    # Construct parameters
    query_parameters = {}
    if snapshot is not None:
        query_parameters['snapshot'] = client._serialize.query("snapshot", snapshot, 'str')  # pylint: disable=protected-access
    if version_id is not None:
        query_parameters['versionid'] = client._serialize.query("version_id", version_id, 'str')  # pylint: disable=protected-access
    if timeout is not None:
        query_parameters['timeout'] = client._serialize.query("timeout", timeout, 'int', minimum=0)  # pylint: disable=protected-access
    query_parameters['comp'] = client._serialize.query("comp", comp, 'str')  # pylint: disable=protected-access, specify-parameter-names-in-call

    # Construct headers
    header_parameters = {}
    header_parameters['x-ms-access-tier'] = client._serialize.header("tier", tier, 'str')  # pylint: disable=protected-access, specify-parameter-names-in-call
    if rehydrate_priority is not None:
        header_parameters['x-ms-rehydrate-priority'] = client._serialize.header(  # pylint: disable=protected-access
            "rehydrate_priority", rehydrate_priority, 'str')
    if lease_id is not None:
        header_parameters['x-ms-lease-id'] = client._serialize.header("lease_id", lease_id, 'str')  # pylint: disable=protected-access
    if if_tags is not None:
        header_parameters['x-ms-if-tags'] = client._serialize.header("if_tags", if_tags, 'str')  # pylint: disable=protected-access

    return query_parameters, header_parameters

def _generate_set_tiers_options(
    query_str: str,
    container_name: str,
    blob_tier: Optional[Union["PremiumPageBlobTier", "StandardBlobTier", str]],
    client: AzureBlobStorage,
    *blobs: Union[str, Dict[str, Any], BlobProperties],
    **kwargs: Any
) -> Tuple[List[HttpRequest], Dict[str, Any]]:
    """Creates a dictionary containing the options for a set tiers operation.

    :param str query_str:
        The query string of the endpoint URL.
    :param str container_name:
        The name of the container.
    :param blob_tier:
        Indicates the tier to be set on the blobs.
    :type blob_tier: Optional[Union["PremiumPageBlobTier", "StandardBlobTier", str]]
    :param AzureBlobStorage client:
        The generated Blob Storage client.
    :param blobs:
            The blobs to delete. This can be a single blob, or multiple values can
            be supplied, where each value is either the name of the blob (str) or BlobProperties.

            .. note::
                When the blob type is dict, here's a list of keys, value rules.

                blob name:
                    key: 'name', value type: str
                snapshot you want to delete:
                    key: 'snapshot', value type: str
                version id:
                    key: 'version_id', value type: str
                whether to delete snapshots when deleting blob:
                    key: 'delete_snapshots', value: 'include' or 'only'
                if the blob modified or not:
                    key: 'if_modified_since', 'if_unmodified_since', value type: datetime
                etag:
                    key: 'etag', value type: str
                match the etag or not:
                    key: 'match_condition', value type: MatchConditions
                tags match condition:
                    key: 'if_tags_match_condition', value type: str
                lease:
                    key: 'lease_id', value type: Union[str, LeaseClient]
                timeout for subrequest:
                    key: 'timeout', value type: int

    :type blobs: Union[str, Dict[str, Any], BlobProperties]
    :returns: A tuple containing the list of HttpRequests and the set tiers options.
    :rtype: Tuple[List[HttpRequest], Dict[str, Any]]
    """
    timeout = kwargs.pop('timeout', None)
    raise_on_any_failure = kwargs.pop('raise_on_any_failure', True)
    rehydrate_priority = kwargs.pop('rehydrate_priority', None)
    if_tags = kwargs.pop('if_tags_match_condition', None)
    kwargs.update({'raise_on_any_failure': raise_on_any_failure,
                    'sas': query_str.replace('?', '&'),
                    'timeout': '&timeout=' + str(timeout) if timeout else "",
                    'path': container_name,
                    'restype': 'restype=container&'
                    })

    reqs = []
    for blob in blobs:
        if not isinstance(blob, str):
            blob_name = blob.get('name')
            tier = blob_tier or blob.get('blob_tier')
            query_parameters, header_parameters = _generate_set_tiers_subrequest_options(
                client=client,
                tier=tier,
                snapshot=blob.get('snapshot'),
                version_id=blob.get('version_id'),
                rehydrate_priority=rehydrate_priority or blob.get('rehydrate_priority'),
                lease_access_conditions=blob.get('lease_id'),
                if_tags=if_tags or blob.get('if_tags_match_condition'),
                timeout=timeout or blob.get('timeout')
            )
        else:
            blob_name = blob
            query_parameters, header_parameters = _generate_set_tiers_subrequest_options(
                client, blob_tier, rehydrate_priority=rehydrate_priority, if_tags=if_tags)

        req = HttpRequest(
            "PUT",
            f"/{quote(container_name)}/{quote(str(blob_name), safe='/~')}{query_str}",
            headers=header_parameters
        )
        req.format_parameters(query_parameters)
        reqs.append(req)

    return reqs, kwargs
